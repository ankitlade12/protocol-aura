from typing import Optional

from protocol_aura.agents.base import BaseAgent
from protocol_aura.core.config import settings
from protocol_aura.protocol import (
    AuraMessage,
    AuraQuery,
    AuraOffer,
    AuraCounteroffer,
    AuraAccept,
    AuraReject,
    VibeTransformation,
    ConstraintCheck,
    VibeVector,
    Mandate,
    Constraints,
    OfferBundle,
    vibe_service,
)


class ShopperAgent(BaseAgent):
    def __init__(
        self,
        user_id: str,
        user_name: str,
        mandate: Mandate,
        style_goal: str,
    ):
        super().__init__(agent_id=user_id, name=user_name)
        self.mandate = mandate
        self.style_goal = style_goal
        self.target_vibe: Optional[VibeVector] = None
    
    async def initialize_vibe(self, emotional_prompt: str) -> VibeVector:
        self.target_vibe = await vibe_service.generate_vibe_vector(emotional_prompt)
        return self.target_vibe
    
    async def process_message(self, message: AuraMessage) -> Optional[AuraMessage]:
        self.log_message(message)
        
        if isinstance(message, AuraOffer):
            return self._evaluate_offer(message)
        elif isinstance(message, AuraCounteroffer):
            return self._evaluate_counteroffer(message)
        return None
    
    async def create_query(self, emotional_prompt: str, context: str = "", session_id: str = "") -> AuraQuery:
        if not self.target_vibe:
            await self.initialize_vibe(emotional_prompt)
        
        constraints = Constraints(
            max_budget=self.mandate.budget_cap,
            categories=self.mandate.categories,
        )
        
        return AuraQuery(
            shopper_id=self.agent_id,
            session_id=session_id,
            turn_id=0,
            target_vibe=self.target_vibe,
            emotional_prompt=emotional_prompt,
            constraints=constraints,
            context=context,
        )
    
    def _evaluate_offer(self, offer: AuraOffer) -> AuraMessage:
        option_a = offer.option_a
        option_b = offer.option_b
        
        a_valid = self._check_bundle_valid(option_a)
        b_valid = option_b and self._check_bundle_valid(option_b)
        
        if a_valid and b_valid:
            chosen = option_a if option_a.match_score >= option_b.match_score else option_b
            chosen_label = "A" if chosen == option_a else "B"
        elif a_valid:
            chosen = option_a
            chosen_label = "A"
        elif b_valid:
            chosen = option_b
            chosen_label = "B"
        else:
            return AuraReject(
                sender_id=self.agent_id,
                recipient_id=offer.store_id,
                session_id=offer.session_id,
                turn_id=offer.turn_id + 1,
                in_reply_to=offer.message_id,
                reason=self._get_rejection_reason(option_a, option_b),
                constraint_violations=[c for c in option_a.constraint_checks if not c.satisfied],
                would_accept_if=f"Budget increased to ${option_b.total_price:.0f}" if option_b else "Lower-priced alternatives available",
            )
        
        return AuraAccept(
            shopper_id=self.agent_id,
            store_id=offer.store_id,
            session_id=offer.session_id,
            turn_id=offer.turn_id + 1,
            in_reply_to=offer.message_id,
            accepted_bundle=chosen_label,
            accepted_products=chosen.products,
            final_vibe=chosen.achievable_vibe or VibeVector(embedding=[], axes={}, description=""),
            total_price=chosen.total_price,
            transformations_accepted=chosen.transformations,
            constraint_checks=chosen.constraint_checks,
        )
    
    def _evaluate_counteroffer(self, counteroffer: AuraCounteroffer) -> AuraMessage:
        budget_ok = all(c.satisfied for c in counteroffer.constraint_checks if c.constraint == "budget")
        match_ok = counteroffer.match_score >= settings.similarity_threshold
        
        if budget_ok and match_ok:
            return AuraAccept(
                shopper_id=self.agent_id,
                store_id=counteroffer.store_id,
                session_id=counteroffer.session_id,
                turn_id=counteroffer.turn_id + 1,
                in_reply_to=counteroffer.message_id,
                accepted_bundle="A",
                accepted_products=counteroffer.proposed_products,
                final_vibe=counteroffer.achievable_vibe,
                total_price=sum(p.price for p in counteroffer.proposed_products),
                transformations_accepted=counteroffer.transformations,
                constraint_checks=counteroffer.constraint_checks,
            )
        
        violations = [c for c in counteroffer.constraint_checks if not c.satisfied]
        return AuraReject(
            sender_id=self.agent_id,
            recipient_id=counteroffer.store_id,
            session_id=counteroffer.session_id,
            turn_id=counteroffer.turn_id + 1,
            in_reply_to=counteroffer.message_id,
            reason="Budget constraint violated" if not budget_ok else f"Match score {counteroffer.match_score:.0%} below threshold",
            constraint_violations=violations,
            would_accept_if="Lower-priced alternatives" if not budget_ok else "Higher vibe alignment",
        )
    
    def _check_bundle_valid(self, bundle: OfferBundle) -> bool:
        budget_ok = all(c.satisfied for c in bundle.constraint_checks if c.constraint == "budget")
        match_ok = bundle.match_score >= 0.50
        return budget_ok and match_ok
    
    def _get_rejection_reason(self, option_a: OfferBundle, option_b: Optional[OfferBundle]) -> str:
        a_violations = [c for c in option_a.constraint_checks if not c.satisfied]
        if a_violations:
            return f"Option A: {a_violations[0].message}"
        if option_b:
            b_violations = [c for c in option_b.constraint_checks if not c.satisfied]
            if b_violations:
                return f"Both options violate constraints. Option B: {b_violations[0].message}"
        return "No valid options within constraints"
