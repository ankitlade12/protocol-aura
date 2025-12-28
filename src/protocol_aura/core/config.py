import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    embedding_model: str = Field(default="models/text-embedding-004", description="Embedding model")
    llm_model: str = Field(default="gemini-1.5-flash", description="LLM model for agent reasoning")
    
    vibe_dimensions: int = Field(default=768, description="Dimensionality of vibe vectors")
    negotiation_max_rounds: int = Field(default=5, description="Maximum negotiation rounds")
    similarity_threshold: float = Field(default=0.75, description="Minimum similarity for match")
    
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    demo_mode: bool = Field(default=True, description="Use demo mode without API calls")
    
    class Config:
        env_file = ".env"
        env_prefix = "AURA_"


settings = Settings()
