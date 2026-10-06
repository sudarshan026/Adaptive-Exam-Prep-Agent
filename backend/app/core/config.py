"""Core configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./exam_prep.db"
    
    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    
    # Groq API
    GROQ_API_KEY: Optional[str] = None
    
    # YouTube API
    YOUTUBE_API_KEY: Optional[str] = None
    
    # Application
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_demo_mode(self) -> bool:
        """App runs in demo mode when no Groq API key is configured."""
        return not self.GROQ_API_KEY or self.GROQ_API_KEY.strip() == ""
    
    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
