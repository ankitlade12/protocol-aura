from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from protocol_aura.agents import BoutiqueAgent, ShopperAgent
from protocol_aura.protocol import (
    AuraMessage,
    AuraQuery,
    AuraOffer,
    AuraCounteroffer,
    AuraAccept,
    AuraReject,
    MessageType,
    ConstraintCheck,
)


class NegotiationStatus(str, Enum):
    PENDING = "pending"
    QUERIED = "queried"
    RESPONDED = "responded"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class TurnOutcome(str, Enum):
    OFFER_SENT = "offer_sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTER = "counter"


class NegotiationRound(BaseModel):
    round_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    shopper_message: Optional[AuraMessage] = None
    store_message: Optional[AuraMessage] = None
    outcome: TurnOutcome = TurnOutcome.OFFER_SENT
    notes: str = ""


class NegotiationSession(BaseModel):
    session_id: str
    shopper_id: str
    store_id: str
    store_name: str = ""
    emotional_prompt: str
    status: NegotiationStatus = NegotiationStatus.PENDING
    rounds: list[NegotiationRound] = Field(default_factory=list)
    final_result: Optional[AuraMessage] = None
    match_score: float = 0.0
    latency_ms: int = 0
    turns_used: int = 0
    max_turns: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class NegotiationEngine:
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
        self.sessions: dict[str, NegotiationSession] = {}
    
    async def start_negotiation(
        self,
        shopper: ShopperAgent,
        boutique: BoutiqueAgent,
        emotional_prompt: str,
        context: str = "",
    ) -> NegotiationSession:
        session_id = str(uuid.uuid4())
        
        session = NegotiationSession(
            session_id=session_id,
            shopper_id=shopper.agent_id,
            store_id=boutique.agent_id,
            store_name=boutique.name,
            emotional_prompt=emotional_prompt,
            status=NegotiationStatus.QUERIED,
            max_turns=self.max_rounds,
        )
        self.sessions[session_id] = session
        
        query = await shopper.create_query(emotional_prompt, context, session_id)
        
        round_1 = NegotiationRound(round_number=1)
        round_1.shopper_message = query
        
        offer = await boutique.process_message(query)
        round_1.store_message = offer
        round_1.outcome = TurnOutcome.OFFER_SENT
        
        if isinstance(offer, AuraOffer):
            session.match_score = max(offer.option_a.match_score, offer.option_b.match_score if offer.option_b else 0)
            session.latency_ms = offer.latency_ms
            round_1.notes = f"Options: A={offer.option_a.match_score:.0%}, B={offer.option_b.match_score:.0%}" if offer.option_b else f"Option A: {offer.option_a.match_score:.0%}"
        
        session.rounds.append(round_1)
        session.status = NegotiationStatus.RESPONDED
        session.turns_used = 1
        
        shopper_response = await shopper.process_message(offer)
        
        round_2 = NegotiationRound(round_number=2)
        round_2.shopper_message = shopper_response
        
        if isinstance(shopper_response, AuraAccept):
            round_2.outcome = TurnOutcome.ACCEPTED
            round_2.notes = f"Accepted bundle {shopper_response.accepted_bundle}: ${shopper_response.total_price:.0f}"
            session.status = NegotiationStatus.ACCEPTED
            session.final_result = shopper_response
        elif isinstance(shopper_response, AuraReject):
            round_2.outcome = TurnOutcome.REJECTED
            round_2.notes = f"Rejected: {shopper_response.reason}"
            if shopper_response.would_accept_if:
                round_2.notes += f" | Would accept if: {shopper_response.would_accept_if}"
            session.status = NegotiationStatus.REJECTED
            session.final_result = shopper_response
        else:
            session.status = NegotiationStatus.ACCEPTED
            if isinstance(offer, AuraOffer):
                session.final_result = AuraAccept(
                    shopper_id=shopper.agent_id,
                    store_id=boutique.agent_id,
                    session_id=session_id,
                    turn_id=2,
                    accepted_bundle="A",
                    accepted_products=offer.option_a.products,
                    final_vibe=offer.option_a.achievable_vibe,
                    total_price=offer.option_a.total_price,
                    transformations_accepted=offer.option_a.transformations,
                    constraint_checks=offer.option_a.constraint_checks,
                )
        
        session.rounds.append(round_2)
        session.turns_used = 2
        session.updated_at = datetime.utcnow()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        return self.sessions.get(session_id)
    
    def get_transcript(self, session: NegotiationSession) -> list[dict]:
        transcript = []
        
        for round_data in session.rounds:
            if round_data.shopper_message:
                msg = round_data.shopper_message
                if isinstance(msg, AuraQuery):
                    transcript.append({
                        "speaker": "Shopper",
                        "type": "QUERY",
                        "turn": round_data.round_number,
                        "content": f"Looking for: \"{msg.emotional_prompt}\"",
                        "details": {
                            "budget": f"${msg.constraints.max_budget:.0f}",
                            "vibe": msg.target_vibe.description if msg.target_vibe else "",
                        }
                    })
                elif isinstance(msg, AuraAccept):
                    transcript.append({
                        "speaker": "Shopper",
                        "type": "ACCEPT",
                        "turn": round_data.round_number,
                        "content": f"✓ Accepted Option {msg.accepted_bundle}: {len(msg.accepted_products)} items for ${msg.total_price:.0f}",
                        "details": {
                            "products": [p.name for p in msg.accepted_products],
                            "transformations": [t.reason for t in msg.transformations_accepted],
                        }
                    })
                elif isinstance(msg, AuraReject):
                    transcript.append({
                        "speaker": "Shopper",
                        "type": "REJECT",
                        "turn": round_data.round_number,
                        "content": f"✗ {msg.reason}",
                        "details": {
                            "would_accept_if": msg.would_accept_if,
                            "violations": [c.message for c in msg.constraint_violations],
                        }
                    })
            
            if round_data.store_message:
                msg = round_data.store_message
                if isinstance(msg, AuraOffer):
                    opt_a = msg.option_a
                    opt_b = msg.option_b
                    
                    options_text = f"**Option A** ({opt_a.bundle_type}): {opt_a.match_score:.0%} match, ${opt_a.total_price:.0f}, distance {opt_a.vibe_distance:.0%}"
                    if opt_b:
                        options_text += f"\n**Option B** ({opt_b.bundle_type}): {opt_b.match_score:.0%} match, ${opt_b.total_price:.0f}, distance {opt_b.vibe_distance:.0%}"
                    
                    transcript.append({
                        "speaker": session.store_name,
                        "type": "OFFER",
                        "turn": round_data.round_number,
                        "content": msg.message,
                        "details": {
                            "options": options_text,
                            "recommended": msg.recommended,
                            "option_a": {
                                "products": [p.name for p in opt_a.products],
                                "match": f"{opt_a.match_score:.0%}",
                                "price": f"${opt_a.total_price:.0f}",
                                "distance": f"{opt_a.vibe_distance:.0%}",
                                "budget_ok": all(c.satisfied for c in opt_a.constraint_checks),
                            },
                            "option_b": {
                                "products": [p.name for p in opt_b.products] if opt_b else [],
                                "match": f"{opt_b.match_score:.0%}" if opt_b else "N/A",
                                "price": f"${opt_b.total_price:.0f}" if opt_b else "N/A",
                                "distance": f"{opt_b.vibe_distance:.0%}" if opt_b else "N/A",
                                "budget_ok": all(c.satisfied for c in opt_b.constraint_checks) if opt_b else False,
                            } if opt_b else None,
                            "transformations": [
                                f"{t.axis}: {t.from_value:.0%}→{t.to_value:.0%} ({t.direction}{abs(t.delta):.0%}) — {t.item_change}"
                                for t in opt_a.transformations
                            ],
                            "latency_ms": msg.latency_ms,
                        }
                    })
        
        return transcript


negotiation_engine = NegotiationEngine()
