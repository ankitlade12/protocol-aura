from typing import Optional
import json
import random
import time

from protocol_aura.core.config import settings
from protocol_aura.protocol.models import VibeVector, VibeAxis


class VibeEmbeddingService:
    def __init__(self):
        self._embeddings = None
        self._llm = None
        self._initialized = False
    
    def _ensure_initialized(self):
        if self._initialized:
            return
        
        if settings.demo_mode:
            self._initialized = True
            return
        
        if not settings.gemini_api_key:
            raise ValueError("AURA_GEMINI_API_KEY environment variable is required")
        
        import google.generativeai as genai
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        genai.configure(api_key=settings.gemini_api_key)
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.gemini_api_key,
        )
        model_name = settings.llm_model
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        self._llm = genai.GenerativeModel(model_name)
        self._initialized = True
    
    async def generate_vibe_vector(self, text: str) -> VibeVector:
        self._ensure_initialized()
        
        time.sleep(random.uniform(0.1, 0.3))
        
        if settings.demo_mode:
            return self._generate_demo_vibe(text)
        
        embedding = await self._get_embedding(text)
        axes = await self._extract_vibe_axes(text)
        description = await self._generate_vibe_description(text, axes)
        return VibeVector(
            embedding=embedding,
            axes=axes,
            description=description,
        )
    
    def _generate_demo_vibe(self, text: str) -> VibeVector:
        text_lower = text.lower()
        
        axes = {
            "rebellion": 0.50,
            "minimalism": 0.50,
            "nostalgia": 0.50,
            "power": 0.50,
            "warmth": 0.50,
            "chaos": 0.50,
            "elegance": 0.50,
            "playfulness": 0.50,
        }
        
        if any(w in text_lower for w in ["ceo", "executive", "board", "corporate"]):
            axes["power"] = 0.88
            axes["elegance"] = 0.82
            axes["rebellion"] = 0.35
            axes["playfulness"] = 0.25
        
        if any(w in text_lower for w in ["code", "tech", "cyber", "future", "modern", "sleek", "night"]):
            axes["rebellion"] = 0.72
            axes["minimalism"] = 0.68
            axes["nostalgia"] = 0.18
            axes["power"] = 0.75
        
        if any(w in text_lower for w in ["dj", "club", "party", "rave"]):
            axes["chaos"] = 0.65
            axes["playfulness"] = 0.70
            axes["rebellion"] = 0.75
        
        if any(w in text_lower for w in ["vintage", "retro", "1920", "classic", "antique", "jazz"]):
            axes["nostalgia"] = 0.92
            axes["warmth"] = 0.78
            axes["elegance"] = 0.75
            axes["chaos"] = 0.25
        
        if any(w in text_lower for w in ["chaos", "wild", "crazy", "goblin", "maximalist"]):
            axes["chaos"] = 0.92
            axes["playfulness"] = 0.88
            axes["minimalism"] = 0.08
            axes["rebellion"] = 0.85
        
        if any(w in text_lower for w in ["warm", "cozy", "friendly", "inviting", "garden"]):
            axes["warmth"] = 0.85
            axes["playfulness"] = 0.60
        
        if any(w in text_lower for w in ["elegant", "refined", "sophisticated", "luxury", "premium"]):
            axes["elegance"] = 0.88
            axes["chaos"] = 0.15
        
        if any(w in text_lower for w in ["minimal", "clean", "simple", "sparse", "monk"]):
            axes["minimalism"] = 0.88
            axes["chaos"] = 0.12
            axes["elegance"] = 0.70
        
        if any(w in text_lower for w in ["rebel", "punk", "edge", "alternative"]):
            axes["rebellion"] = 0.88
            axes["elegance"] = 0.35
        
        if any(w in text_lower for w in ["dinner", "hosting"]):
            axes["elegance"] = 0.72
            axes["warmth"] = 0.75
        
        for axis in axes:
            noise = random.uniform(-0.03, 0.03)
            axes[axis] = round(max(0.05, min(0.95, axes[axis] + noise)), 2)
        
        dominant = sorted(axes.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)[:3]
        desc_parts = []
        for axis, val in dominant:
            if val >= 0.70:
                desc_parts.append(f"strong {axis}")
            elif val <= 0.30:
                desc_parts.append(f"minimal {axis}")
        
        description = f"Aesthetic blend: {', '.join(desc_parts)}" if desc_parts else "Balanced aesthetic profile"
        
        embedding = [round(random.gauss(0, 0.1), 4) for _ in range(768)]
        
        return VibeVector(
            embedding=embedding,
            axes=axes,
            description=description,
        )
    
    async def _get_embedding(self, text: str) -> list[float]:
        self._ensure_initialized()
        result = self._embeddings.embed_query(text)
        return result
    
    async def _extract_vibe_axes(self, text: str) -> dict[str, float]:
        self._ensure_initialized()
        prompt = f"""Analyze this aesthetic description and score it on these vibe axes.
Return a JSON object with scores from 0.0 to 1.0 for each axis.

Axes (all 0.0 to 1.0):
- rebellion: 0=conformist, 1=rebellious
- minimalism: 0=maximalist, 1=minimalist
- nostalgia: 0=futuristic, 1=vintage
- power: 0=soft/gentle, 1=powerful/bold
- warmth: 0=cold/distant, 1=warm/inviting
- chaos: 0=structured, 1=chaotic
- elegance: 0=rough/raw, 1=elegant
- playfulness: 0=serious, 1=playful

Description: {text}

Return ONLY valid JSON like: {{"rebellion": 0.7, "minimalism": 0.3, ...}}"""

        response = self._llm.generate_content(prompt)
        try:
            json_str = response.text.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {axis.value: 0.5 for axis in VibeAxis}
    
    async def _generate_vibe_description(
        self, original_text: str, axes: dict[str, float]
    ) -> str:
        self._ensure_initialized()
        dominant_axes = sorted(axes.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)[:3]
        axes_str = ", ".join([f"{k}: {v:.2f}" for k, v in dominant_axes])
        
        prompt = f"""Create a one-sentence poetic description of this aesthetic vibe.

Original: {original_text}
Dominant traits: {axes_str}

Be evocative and concise. One sentence only."""

        response = self._llm.generate_content(prompt)
        return response.text.strip()
    
    def compute_similarity(self, v1: VibeVector, v2: VibeVector) -> float:
        return v1.similarity(v2)


vibe_service = VibeEmbeddingService()
