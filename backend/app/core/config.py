"""
Configuration management for the Website Intelligence API.
Handles environment variables and application settings.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_secret_key: str = Field(..., env="API_SECRET_KEY")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # LLM APIs
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Database
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    
    # Vector Database
    qdrant_url: Optional[str] = Field(default=None, env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    
    # External Services
    jina_ai_api_key: Optional[str] = Field(default=None, env="JINA_AI_API_KEY")
    
    # Scraping Configuration
    min_text_length: int = Field(default=500, env="MIN_TEXT_LENGTH")
    min_text_ratio: float = Field(default=0.1, env="MIN_TEXT_RATIO")
    min_keyword_matches: int = Field(default=2, env="MIN_KEYWORD_MATCHES")
    scraping_timeout: int = Field(default=10, env="SCRAPING_TIMEOUT")
    
    # Rate Limiting
    analyze_rate_limit: str = Field(default="10/minute", env="ANALYZE_RATE_LIMIT")
    chat_rate_limit: str = Field(default="30/minute", env="CHAT_RATE_LIMIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
