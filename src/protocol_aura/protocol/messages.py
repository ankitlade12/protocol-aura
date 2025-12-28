from datetime import datetime
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field
import uuid

from protocol_aura.protocol.models import (
    VibeVector,
    BrandManifold,
    Constraints,
    ConstraintCheck,
    Product,
)


class MessageType(str, Enum):
    AURA_PROFILE = "AURA_PROFILE"
    AURA_QUERY = "AURA_QUERY"
    AURA_OFFER = "AURA_OFFER"
    AURA_COUNTER = "AURA_COUNTER"
    AURA_ACCEPT = "AURA_ACCEPT"
    AURA_REJECT = "AURA_REJECT"


class MessageStatus(str, Enum):
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    RESPONDED = "responded"
    FAILED = "failed"


class VibeTransformation(BaseModel):
    axis: str
    from_value: float = Field(ge=0.0, le=1.0)
    to_value: float = Field(ge=0.0, le=1.0)
    delta: float
    direction: str
    reason: str
    item_change: str = Field(default="")


class OfferBundle(BaseModel):
    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    bundle_type: str
    products: list[Product]
    total_price: float
    match_score: float = Field(ge=0.0, le=1.0)
    vibe_distance: float
    constraint_checks: list[ConstraintCheck] = Field(default_factory=list)
    transformations: list[VibeTransformation] = Field(default_factory=list)
    achievable_vibe: Optional[VibeVector] = None
    summary: str = ""


class AuraProfile(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AURA_PROFILE
    store_id: str
    session_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    manifold: BrandManifold
    featured_products: list[Product] = Field(default_factory=list)
    negotiation_flexibility: float = Field(default=0.5, ge=0.0, le=1.0)


class AuraQuery(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AURA_QUERY
    shopper_id: str
    session_id: str = ""
    turn_id: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_vibe: VibeVector
    emotional_prompt: str
    constraints: Constraints = Field(default_factory=Constraints)
    context: str = ""
    ttl_ms: int = Field(default=4000)


class AuraOffer(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AURA_OFFER
    store_id: str
    shopper_id: str
    session_id: str = ""
    turn_id: int = 0
    in_reply_to: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: MessageStatus = MessageStatus.RESPONDED
    
    option_a: OfferBundle = Field(description="Budget-fit option")
    option_b: Optional[OfferBundle] = Field(default=None, description="Vibe-fit option")
    
    recommended: str = Field(default="A", description="Which option store recommends")
    message: str = ""
    latency_ms: int = 0


class AuraCounteroffer(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AURA_COUNTER
    store_id: str
    shopper_id: str
    session_id: str = ""
    turn_id: int = 0
    in_reply_to: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: MessageStatus = MessageStatus.RESPONDED
    match_score: float = Field(ge=0.0, le=1.0)
    proposed_products: list[Product]
    transformations: list[VibeTransformation] = Field(default_factory=list)
    budget_adjustment: float = 0.0
    message: str = ""
    achievable_vibe: VibeVector
    constraint_checks: list[ConstraintCheck] = Field(default_factory=list)
    latency_ms: int = 0


class AuraAccept(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AURA_ACCEPT
    shopper_id: str
    store_id: str
    session_id: str = ""
    turn_id: int = 0
    in_reply_to: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    accepted_bundle: str = Field(default="A")
    accepted_products: list[Product]
    final_vibe: VibeVector
    total_price: float
    transformations_accepted: list[VibeTransformation] = Field(default_factory=list)
    constraint_checks: list[ConstraintCheck] = Field(default_factory=list)


class AuraReject(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.AURA_REJECT
    sender_id: str
    recipient_id: str
    session_id: str = ""
    turn_id: int = 0
    in_reply_to: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: str
    constraint_violations: list[ConstraintCheck] = Field(default_factory=list)
    would_accept_if: str = ""


AuraMessage = Union[AuraProfile, AuraQuery, AuraOffer, AuraCounteroffer, AuraAccept, AuraReject]
