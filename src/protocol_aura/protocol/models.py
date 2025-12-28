from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import numpy as np
import uuid


class VibeAxis(str, Enum):
    REBELLION = "rebellion"
    MINIMALISM = "minimalism"
    NOSTALGIA = "nostalgia"
    POWER = "power"
    WARMTH = "warmth"
    CHAOS = "chaos"
    ELEGANCE = "elegance"
    PLAYFULNESS = "playfulness"


class VibeVector(BaseModel):
    embedding: list[float] = Field(description="Raw embedding vector from LLM")
    axes: dict[str, float] = Field(
        default_factory=dict,
        description="Interpretable vibe axes with scores (0.0 to 1.0)"
    )
    description: str = Field(default="", description="Human-readable vibe description")
    
    def similarity(self, other: "VibeVector") -> float:
        if not self.axes or not other.axes:
            return 0.5
        
        total_diff = 0.0
        count = 0
        for axis in self.axes:
            if axis in other.axes:
                diff = abs(self.axes[axis] - other.axes[axis])
                total_diff += diff
                count += 1
        
        if count == 0:
            return 0.5
        
        avg_diff = total_diff / count
        return max(0.0, min(1.0, 1.0 - avg_diff))


class Product(BaseModel):
    id: str
    name: str
    price: float
    category: str
    description: str
    vibe_vector: Optional[VibeVector] = None
    image_url: Optional[str] = None
    stock: int = 0
    attributes: dict[str, str] = Field(default_factory=dict)


class BrandManifold(BaseModel):
    store_id: str
    store_name: str
    vibe_center: VibeVector = Field(description="Central brand aesthetic")
    vibe_boundaries: dict[str, tuple[float, float]] = Field(
        default_factory=dict,
        description="Allowed ranges for each vibe axis"
    )
    style_tags: list[str] = Field(default_factory=list)
    products: list[Product] = Field(default_factory=list)
    
    def contains_vibe(self, vibe: VibeVector) -> bool:
        for axis, (low, high) in self.vibe_boundaries.items():
            if axis in vibe.axes:
                if not (low <= vibe.axes[axis] <= high):
                    return False
        return True


class Constraints(BaseModel):
    max_budget: float = Field(default=float("inf"))
    min_rating: float = Field(default=0.0)
    categories: list[str] = Field(default_factory=list)
    materials_exclude: list[str] = Field(default_factory=list)
    delivery_days_max: int = Field(default=14)


class ConstraintCheck(BaseModel):
    constraint: str
    satisfied: bool
    actual_value: str
    required_value: str
    message: str


class Mandate(BaseModel):
    user_id: str
    budget_cap: float
    categories: list[str] = Field(default_factory=list)
    merchant_allowlist: list[str] = Field(default_factory=list)
    auto_purchase_enabled: bool = False
    max_item_price: float = Field(default=500.0)
    require_return_policy: bool = True
