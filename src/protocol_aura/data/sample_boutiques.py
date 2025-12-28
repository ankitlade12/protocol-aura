from protocol_aura.protocol import (
    VibeVector,
    VibeAxis,
    Product,
    BrandManifold,
    Constraints,
    Mandate,
)


def create_cyber_noir_boutique() -> BrandManifold:
    vibe = VibeVector(
        embedding=[0.0] * 768,
        axes={
            "rebellion": 0.75,
            "minimalism": 0.70,
            "nostalgia": 0.15,
            "power": 0.85,
            "warmth": 0.25,
            "chaos": 0.35,
            "elegance": 0.80,
            "playfulness": 0.20,
        },
        description="Dark futurism meets sleek architecture - chrome and shadow in perfect tension",
    )
    
    products = [
        Product(
            id="cn001",
            name="Obsidian Matrix Blazer",
            price=289.00,
            category="outerwear",
            description="Structured blazer with subtle metallic threading",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"rebellion": 0.65, "power": 0.90, "elegance": 0.85, "minimalism": 0.70},
                description="Corporate power with an edge",
            ),
            stock=12,
            attributes={"material": "wool-blend", "threading": "metallic", "fit": "structured"},
        ),
        Product(
            id="cn002",
            name="Chrome Shadow Boots",
            price=345.00,
            category="footwear",
            description="Matte black boots with chrome heel accent",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"rebellion": 0.75, "power": 0.80, "elegance": 0.70, "minimalism": 0.65},
                description="Walk through the future",
            ),
            stock=8,
            attributes={"material": "leather", "heel": "chrome accent", "finish": "matte"},
        ),
        Product(
            id="cn003",
            name="Neural Link Pendant",
            price=125.00,
            category="accessories",
            description="Geometric titanium pendant on silk cord",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"rebellion": 0.55, "power": 0.60, "elegance": 0.90, "minimalism": 0.80},
                description="Subtle tech elegance",
            ),
            stock=25,
            attributes={"material": "titanium", "chain": "silk cord", "style": "geometric"},
        ),
        Product(
            id="cn004",
            name="Midnight Code Tee",
            price=85.00,
            category="tops",
            description="Premium cotton tee with subtle circuit pattern",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"rebellion": 0.60, "power": 0.50, "elegance": 0.55, "minimalism": 0.75},
                description="Casual tech aesthetic",
            ),
            stock=30,
            attributes={"material": "premium cotton", "pattern": "circuit", "fit": "relaxed"},
        ),
    ]
    
    return BrandManifold(
        store_id="cyber-noir",
        store_name="NEXUS",
        vibe_center=vibe,
        vibe_boundaries={
            "rebellion": (0.50, 1.0),
            "minimalism": (0.50, 0.90),
            "power": (0.60, 1.0),
            "warmth": (0.10, 0.40),
        },
        style_tags=["cyberpunk", "tech-wear", "dark-futurism", "architectural"],
        products=products,
    )


def create_vintage_romantic_boutique() -> BrandManifold:
    vibe = VibeVector(
        embedding=[0.0] * 768,
        axes={
            "rebellion": 0.25,
            "minimalism": 0.30,
            "nostalgia": 0.90,
            "power": 0.40,
            "warmth": 0.85,
            "chaos": 0.25,
            "elegance": 0.80,
            "playfulness": 0.55,
        },
        description="Whispered memories of garden parties and love letters sealed with wax",
    )
    
    products = [
        Product(
            id="vr001",
            name="Heirloom Lace Blouse",
            price=185.00,
            category="tops",
            description="Ivory cotton blouse with antique lace collar",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"nostalgia": 0.90, "warmth": 0.75, "elegance": 0.85, "playfulness": 0.45},
                description="Grandmother's treasured piece",
            ),
            stock=6,
            attributes={"material": "cotton", "collar": "antique lace", "color": "ivory"},
        ),
        Product(
            id="vr002",
            name="Rose Garden Midi Skirt",
            price=165.00,
            category="bottoms",
            description="Flowing skirt with vintage floral print",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"nostalgia": 0.85, "warmth": 0.90, "elegance": 0.70, "playfulness": 0.60},
                description="Dancing through wildflowers",
            ),
            stock=10,
            attributes={"material": "cotton-blend", "print": "vintage floral", "length": "midi"},
        ),
        Product(
            id="vr003",
            name="Pearl Drop Earrings",
            price=95.00,
            category="accessories",
            description="Freshwater pearls on vintage gold settings",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"nostalgia": 0.80, "warmth": 0.65, "elegance": 0.95, "playfulness": 0.35},
                description="Timeless grace",
            ),
            stock=15,
            attributes={"material": "freshwater pearl", "setting": "vintage gold", "style": "drop"},
        ),
    ]
    
    return BrandManifold(
        store_id="vintage-romantic",
        store_name="Maison Éternelle",
        vibe_center=vibe,
        vibe_boundaries={
            "nostalgia": (0.60, 1.0),
            "warmth": (0.50, 1.0),
            "elegance": (0.60, 1.0),
            "rebellion": (0.10, 0.40),
        },
        style_tags=["vintage", "romantic", "cottagecore", "heirloom"],
        products=products,
    )


def create_chaotic_maximalist_boutique() -> BrandManifold:
    vibe = VibeVector(
        embedding=[0.0] * 768,
        axes={
            "rebellion": 0.90,
            "minimalism": 0.10,
            "nostalgia": 0.45,
            "power": 0.70,
            "warmth": 0.60,
            "chaos": 0.95,
            "elegance": 0.40,
            "playfulness": 0.90,
        },
        description="A kaleidoscope explosion of pattern, color, and confident mayhem",
    )
    
    products = [
        Product(
            id="cm001",
            name="Chaos Theory Jacket",
            price=425.00,
            category="outerwear",
            description="Patchwork jacket with 12 different patterns",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"chaos": 0.95, "playfulness": 0.90, "rebellion": 0.85, "warmth": 0.55},
                description="Controlled explosion you can wear",
            ),
            stock=4,
            attributes={"material": "mixed fabrics", "pattern": "12-patch", "style": "statement"},
        ),
        Product(
            id="cm002",
            name="Neon Dreams Platform Boots",
            price=275.00,
            category="footwear",
            description="Holographic platform boots with LED accents",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"chaos": 0.80, "playfulness": 0.95, "rebellion": 0.90, "power": 0.70},
                description="Walking rave party",
            ),
            stock=7,
            attributes={"material": "synthetic", "feature": "LED accents", "heel": "platform"},
        ),
        Product(
            id="cm003",
            name="Statement Maximalist Ring Set",
            price=145.00,
            category="accessories",
            description="Set of 8 mismatched chunky rings",
            vibe_vector=VibeVector(
                embedding=[0.0] * 768,
                axes={"chaos": 0.85, "playfulness": 0.80, "rebellion": 0.70, "warmth": 0.60},
                description="More is more is more",
            ),
            stock=20,
            attributes={"material": "mixed metals", "count": "8 pieces", "style": "chunky"},
        ),
    ]
    
    return BrandManifold(
        store_id="chaotic-maximalist",
        store_name="CTRL+ALT+STYLE",
        vibe_center=vibe,
        vibe_boundaries={
            "chaos": (0.70, 1.0),
            "playfulness": (0.60, 1.0),
            "minimalism": (0.0, 0.30),
            "rebellion": (0.60, 1.0),
        },
        style_tags=["maximalist", "avant-garde", "eclectic", "statement"],
        products=products,
    )


SAMPLE_BOUTIQUES = {
    "cyber-noir": create_cyber_noir_boutique,
    "vintage-romantic": create_vintage_romantic_boutique,
    "chaotic-maximalist": create_chaotic_maximalist_boutique,
}


def get_all_boutiques() -> list[BrandManifold]:
    return [factory() for factory in SAMPLE_BOUTIQUES.values()]


def get_boutique(store_id: str) -> BrandManifold:
    if store_id in SAMPLE_BOUTIQUES:
        return SAMPLE_BOUTIQUES[store_id]()
    raise ValueError(f"Unknown boutique: {store_id}")
