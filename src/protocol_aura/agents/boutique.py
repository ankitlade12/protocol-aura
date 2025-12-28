from typing import Optional
import random
import time
import uuid

from protocol_aura.agents.base import BaseAgent
from protocol_aura.core.config import settings
from protocol_aura.protocol import (
    AuraMessage,
    AuraProfile,
    AuraQuery,
    AuraOffer,
    AuraCounteroffer,
    AuraAccept,
    AuraReject,
    VibeTransformation,
    ConstraintCheck,
    OfferBundle,
    BrandManifold,
    Product,
    VibeVector,
    MessageStatus,
    vibe_service,
)


TRANSFORMATION_ITEMS = {
    "rebellion": {
        "increase": "swap classic hardware → edgy asymmetric buckles",
        "decrease": "choose heritage brass buttons over punk studs",
    },
    "minimalism": {
        "increase": "remove embroidery; switch to clean solid panels",
        "decrease": "add textural layering and detail stitching",
    },
    "nostalgia": {
        "increase": "swap synthetic → vintage-wash cotton",
        "decrease": "switch heritage tweed → modern technical fabric",
    },
    "power": {
        "increase": "reinforce shoulders with structured padding",
        "decrease": "soften silhouette with drop-shoulder construction",
    },
    "warmth": {
        "increase": "shift palette from grey → warm earth tones",
        "decrease": "swap brown accents → cool gunmetal finishes",
    },
    "chaos": {
        "increase": "introduce pattern mixing: add contrast panels",
        "decrease": "unify color story; remove asymmetric elements",
    },
    "elegance": {
        "increase": "upgrade to satin lining and polished hardware",
        "decrease": "embrace raw edges and utilitarian zippers",
    },
    "playfulness": {
        "increase": "add unexpected color pop or whimsical charm",
        "decrease": "remove color accents; go monochrome serious",
    },
}


class BoutiqueAgent(BaseAgent):
    def __init__(
        self,
        store_id: str,
        store_name: str,
        manifold: BrandManifold,
        flexibility: float = 0.5,
    ):
        super().__init__(agent_id=store_id, name=store_name)
        self.manifold = manifold
        self.flexibility = flexibility
    
    async def process_message(self, message: AuraMessage) -> Optional[AuraMessage]:
        self.log_message(message)
        
        if isinstance(message, AuraQuery):
            return await self._handle_query(message)
        return None
    
    async def _handle_query(self, query: AuraQuery) -> AuraOffer:
        start_time = time.time()
        time.sleep(random.uniform(0.12, 0.35))
        
        option_a = self._build_budget_fit_bundle(query)
        option_b = self._build_vibe_fit_bundle(query) if option_a.total_price != query.constraints.max_budget else None
        
        if option_b and option_b.match_score > option_a.match_score + 0.05:
            recommended = "B"
        else:
            recommended = "A"
        
        message = self._generate_offer_message(query, option_a, option_b, recommended)
        latency_ms = int((time.time() - start_time) * 1000)
        
        offer = AuraOffer(
            store_id=self.agent_id,
            shopper_id=query.shopper_id,
            session_id=query.session_id,
            turn_id=query.turn_id,
            in_reply_to=query.message_id,
            status=MessageStatus.RESPONDED,
            option_a=option_a,
            option_b=option_b,
            recommended=recommended,
            message=message,
            latency_ms=latency_ms,
        )
        self.log_message(offer)
        return offer
    
    def _build_budget_fit_bundle(self, query: AuraQuery) -> OfferBundle:
        budget = query.constraints.max_budget
        products = [p for p in self.manifold.products if p.price <= budget * 0.6]
        products.sort(key=lambda p: p.price)
        
        selected = []
        total = 0.0
        for p in products:
            if total + p.price <= budget:
                selected.append(p)
                total += p.price
            if len(selected) >= 3:
                break
        
        if not selected:
            selected = [min(self.manifold.products, key=lambda p: p.price)]
            total = selected[0].price
        
        transformations = self._compute_transformations(query.target_vibe)
        achievable_vibe = self._apply_transformations(query.target_vibe, transformations)
        vibe_distance = self._compute_distance(query.target_vibe, achievable_vibe)
        vibe_distance = round(vibe_distance, 2)
        match_score = round(1.0 - vibe_distance, 2)
        
        budget_ok = total <= budget
        constraint_checks = [ConstraintCheck(
            constraint="budget",
            satisfied=budget_ok,
            actual_value=f"${total:.0f}",
            required_value=f"≤${budget:.0f}",
            message=f"${total:.0f} within ${budget:.0f} cap" if budget_ok else f"Exceeds by ${total - budget:.0f}",
        )]
        
        return OfferBundle(
            bundle_type="budget_fit",
            products=selected,
            total_price=total,
            match_score=match_score,
            vibe_distance=vibe_distance,
            constraint_checks=constraint_checks,
            transformations=transformations,
            achievable_vibe=achievable_vibe,
            summary=f"Budget-optimized: {len(selected)} items, ${total:.0f}",
        )
    
    def _build_vibe_fit_bundle(self, query: AuraQuery) -> OfferBundle:
        products = sorted(self.manifold.products, key=lambda p: p.price, reverse=True)[:3]
        total = sum(p.price for p in products)
        
        transformations = self._compute_transformations(query.target_vibe, fewer=True)
        achievable_vibe = self._apply_transformations(query.target_vibe, transformations)
        vibe_distance = self._compute_distance(query.target_vibe, achievable_vibe)
        vibe_distance = round(vibe_distance, 2)
        match_score = round(1.0 - vibe_distance, 2)
        
        budget = query.constraints.max_budget
        budget_ok = total <= budget
        over_by = max(0, total - budget)
        
        constraint_checks = [ConstraintCheck(
            constraint="budget",
            satisfied=budget_ok,
            actual_value=f"${total:.0f}",
            required_value=f"≤${budget:.0f}",
            message=f"${total:.0f} within cap" if budget_ok else f"Over by ${over_by:.0f} (+{over_by/budget*100:.0f}%)",
        )]
        
        return OfferBundle(
            bundle_type="vibe_fit",
            products=products,
            total_price=total,
            match_score=match_score,
            vibe_distance=vibe_distance,
            constraint_checks=constraint_checks,
            transformations=transformations,
            achievable_vibe=achievable_vibe,
            summary=f"Vibe-optimized: {len(products)} items, ${total:.0f}",
        )
    
    def _compute_distance(self, target: VibeVector, achievable: VibeVector) -> float:
        import math
        sum_sq = 0.0
        count = 0
        for axis in target.axes:
            if axis in achievable.axes:
                diff = target.axes[axis] - achievable.axes[axis]
                sum_sq += diff * diff
                count += 1
        
        if count == 0:
            return 0.5
        
        l2_dist = math.sqrt(sum_sq)
        match = 1.0 / (1.0 + l2_dist)
        return round(1.0 - match, 2)
    
    def _compute_transformations(self, target_vibe: VibeVector, fewer: bool = False) -> list[VibeTransformation]:
        transformations = []
        target_axes = target_vibe.axes
        store_axes = self.manifold.vibe_center.axes
        
        for axis, target_val in target_axes.items():
            if axis in store_axes:
                store_val = store_axes[axis]
                diff = store_val - target_val
                
                if abs(diff) > 0.12:
                    adjusted_val = target_val + diff * self.flexibility
                    adjusted_val = round(max(0.05, min(0.95, adjusted_val)), 2)
                    
                    delta = round(adjusted_val - target_val, 2)
                    direction = "↑" if delta > 0 else "↓"
                    item_change = TRANSFORMATION_ITEMS.get(axis, {}).get(
                        "increase" if delta > 0 else "decrease",
                        f"adjust {axis}"
                    )
                    
                    transformations.append(VibeTransformation(
                        axis=axis,
                        from_value=round(target_val, 2),
                        to_value=adjusted_val,
                        delta=delta,
                        direction=direction,
                        reason=f"{axis}: {target_val:.0%} → {adjusted_val:.0%} ({direction}{abs(delta):.0%})",
                        item_change=item_change,
                    ))
        
        transformations.sort(key=lambda t: abs(t.delta), reverse=True)
        return transformations[:2] if fewer else transformations[:3]
    
    def _apply_transformations(self, target: VibeVector, transformations: list[VibeTransformation]) -> VibeVector:
        adjusted_axes = {k: round(v, 2) for k, v in target.axes.items()}
        for t in transformations:
            adjusted_axes[t.axis] = t.to_value
        
        return VibeVector(
            embedding=self.manifold.vibe_center.embedding,
            axes=adjusted_axes,
            description=f"Negotiated blend with {self.name}",
        )
    
    def _generate_offer_message(
        self, query: AuraQuery, option_a: OfferBundle, option_b: Optional[OfferBundle], recommended: str
    ) -> str:
        a_ok = all(c.satisfied for c in option_a.constraint_checks)
        b_ok = option_b and all(c.satisfied for c in option_b.constraint_checks)
        
        if option_b and not b_ok:
            over_by = option_b.total_price - query.constraints.max_budget
            return (
                f"Two paths forward:\n"
                f"• **Option A (Budget-fit)**: {option_a.match_score:.0%} match, ${option_a.total_price:.0f}, distance {option_a.vibe_distance:.0%}\n"
                f"• **Option B (Vibe-fit)**: {option_b.match_score:.0%} match, ${option_b.total_price:.0f} (+${over_by:.0f} over cap), distance {option_b.vibe_distance:.0%}\n"
                f"Recommend: **{recommended}**. Option B requires budget increase to ${option_b.total_price:.0f}."
            )
        elif option_b:
            return (
                f"Two options available:\n"
                f"• **Option A**: {option_a.match_score:.0%} match, ${option_a.total_price:.0f}\n"
                f"• **Option B**: {option_b.match_score:.0%} match, ${option_b.total_price:.0f}\n"
                f"Both within budget. Recommend: **{recommended}**."
            )
        else:
            return f"Best option: {option_a.match_score:.0%} match at ${option_a.total_price:.0f}. Distance: {option_a.vibe_distance:.0%}."
    
    def get_profile(self) -> AuraProfile:
        return AuraProfile(
            store_id=self.agent_id,
            manifold=self.manifold,
            featured_products=self.manifold.products[:5],
            negotiation_flexibility=self.flexibility,
        )
