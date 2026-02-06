"""Application configuration using Pydantic Settings"""

import os
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "Daily Feed"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///data/dailyfeed.db"
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama, openai, anthropic
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 120
    
    # Alternative LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    DIGEST_HOUR: int = 8
    DIGEST_MINUTE: int = 0
    
    # Feed Settings
    MAX_ARTICLES_PER_SOURCE: int = 15
    SUMMARY_MAX_LENGTH: int = 500
    CRITIC_MIN_SCORE: int = 7
    MAX_RETRIES: int = 2
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
