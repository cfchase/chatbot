from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # FastAPI Settings
    port: int = Field(default=8000, description="Port to run the application on")
    environment: str = Field(default="development", description="Environment (development, production)")
    
    # Anthropic Settings
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key for Claude")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", description="Anthropic model to use")
    
    # Model Settings
    max_tokens: int = Field(default=1024, description="Maximum tokens for Claude responses")
    temperature: float = Field(default=0.7, description="Temperature for Claude responses")


# Create global settings instance
settings = Settings()