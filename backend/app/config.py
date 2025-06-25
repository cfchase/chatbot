import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # FastAPI Settings
    port: int = Field(default=8000, description="Port to run the application on")
    environment: str = Field(default="development", description="Environment (development, production)")
    
    # Anthropic Settings
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key for Claude")
    
    # Model Settings
    claude_model: str = Field(default="claude-3-sonnet-20240229", description="Claude model to use")
    max_tokens: int = Field(default=1024, description="Maximum tokens for Claude responses")
    temperature: float = Field(default=0.7, description="Temperature for Claude responses")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()