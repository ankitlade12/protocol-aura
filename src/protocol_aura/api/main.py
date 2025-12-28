from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

from protocol_aura.agents import BoutiqueAgent, ShopperAgent
from protocol_aura.protocol import Mandate, VibeVector
from protocol_aura.core.negotiation import negotiation_engine, NegotiationSession
from protocol_aura.core.config import settings
from protocol_aura.data import get_all_boutiques, get_boutique


app = FastAPI(
    title="Protocol: Aura",
    description="Agent-to-Agent Retail Layer for Agentic Commerce",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NegotiationRequest(BaseModel):
    emotional_prompt: str = Field(description="User's emotional/aesthetic goal")
    budget: float = Field(default=500.0, description="Maximum budget")
    context: str = Field(default="", description="Additional context")
    target_stores: list[str] = Field(default_factory=list, description="Specific stores to query")


class NegotiationResponse(BaseModel):
    session_id: str
    status: str
    transcript: list[dict]
    final_products: list[dict]
    match_score: Optional[float] = None
    vibe_report: Optional[dict] = None


class VibeAnalysisRequest(BaseModel):
    text: str


class BoutiqueListResponse(BaseModel):
    boutiques: list[dict]


@app.get("/")
async def root():
    return {
        "name": "Protocol: Aura",
        "version": "0.1.0",
        "description": "Agent-to-Agent Retail Layer - Negotiation over meaning, not metadata",
    }


@app.get("/boutiques", response_model=BoutiqueListResponse)
async def list_boutiques():
    boutiques = get_all_boutiques()
    return BoutiqueListResponse(
        boutiques=[
            {
                "id": b.store_id,
                "name": b.store_name,
                "style_tags": b.style_tags,
                "vibe_description": b.vibe_center.description,
                "product_count": len(b.products),
            }
            for b in boutiques
        ]
    )


@app.get("/boutiques/{store_id}")
async def get_boutique_details(store_id: str):
    try:
        boutique = get_boutique(store_id)
        return {
            "id": boutique.store_id,
            "name": boutique.store_name,
            "style_tags": boutique.style_tags,
            "vibe_center": boutique.vibe_center.model_dump(),
            "vibe_boundaries": boutique.vibe_boundaries,
            "products": [p.model_dump() for p in boutique.products],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/negotiate", response_model=NegotiationResponse)
async def start_negotiation(request: NegotiationRequest):
    mandate = Mandate(
        user_id="demo-user",
        budget_cap=request.budget,
        auto_purchase_enabled=False,
    )
    
    shopper = ShopperAgent(
        user_id="demo-user",
        user_name="Demo Shopper",
        mandate=mandate,
        style_goal=request.emotional_prompt,
    )
    
    target_stores = request.target_stores if request.target_stores else ["cyber-noir", "vintage-romantic", "chaotic-maximalist"]
    
    best_session = None
    best_score = 0.0
    
    for store_id in target_stores:
        try:
            manifold = get_boutique(store_id)
            boutique = BoutiqueAgent(
                store_id=manifold.store_id,
                store_name=manifold.store_name,
                manifold=manifold,
                flexibility=0.6,
            )
            
            session = await negotiation_engine.start_negotiation(
                shopper=shopper,
                boutique=boutique,
                emotional_prompt=request.emotional_prompt,
                context=request.context,
            )
            
            if session.final_result and hasattr(session.final_result, "match_score"):
                if session.final_result.match_score > best_score:
                    best_score = session.final_result.match_score
                    best_session = session
            elif best_session is None:
                best_session = session
                
        except Exception as e:
            continue
    
    if not best_session:
        raise HTTPException(status_code=500, detail="Failed to negotiate with any stores")
    
    transcript = negotiation_engine.get_transcript(best_session)
    
    final_products = []
    match_score = None
    vibe_report = None
    
    if best_session.final_result:
        if hasattr(best_session.final_result, "accepted_products"):
            final_products = [p.model_dump() for p in best_session.final_result.accepted_products]
            match_score = best_score
            vibe_report = {
                "original_prompt": request.emotional_prompt,
                "achieved_vibe": best_session.final_result.final_vibe.model_dump() if best_session.final_result.final_vibe else None,
                "transformations": [
                    t.model_dump() for t in best_session.final_result.transformations_accepted
                ] if hasattr(best_session.final_result, "transformations_accepted") else [],
            }
    
    return NegotiationResponse(
        session_id=best_session.session_id,
        status=best_session.status.value,
        transcript=transcript,
        final_products=final_products,
        match_score=match_score,
        vibe_report=vibe_report,
    )


@app.post("/analyze-vibe")
async def analyze_vibe(request: VibeAnalysisRequest):
    from protocol_aura.protocol import vibe_service
    
    vibe = await vibe_service.generate_vibe_vector(request.text)
    return {
        "description": vibe.description,
        "axes": vibe.axes,
    }


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = negotiation_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "emotional_prompt": session.emotional_prompt,
        "rounds": len(session.rounds),
        "transcript": negotiation_engine.get_transcript(session),
    }


def run():
    uvicorn.run(
        "protocol_aura.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    run()
