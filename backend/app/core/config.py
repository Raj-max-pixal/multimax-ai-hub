"""
Configuration Management.

Provides environment-aware settings via Pydantic Settings.
Configuration sources (in priority order):
1. Environment variables
2. .env file
3. Default values
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "Multimax AI Hub"
    APP_VERSION: str = "0.4.0"
    APP_ENV: str = Field(default="development", alias="APP_ENV")
    APP_SECRET_KEY: str = Field(default="change-me-to-a-random-secret-key", alias="APP_SECRET_KEY")
    APP_DEBUG: bool = Field(default=True, alias="APP_DEBUG")

    # --- Logging ---
    APP_LOG_LEVEL: str = Field(default="INFO", alias="APP_LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", alias="LOG_FORMAT")
    LOG_FILE: str = Field(default="./logs/app.log", alias="LOG_FILE")
    LOG_MAX_BYTES: int = Field(default=10485760, alias="LOG_MAX_BYTES")
    LOG_BACKUP_COUNT: int = Field(default=5, alias="LOG_BACKUP_COUNT")

    # --- Database ---
    # Default: SQLite for zero-budget local development
    # Override with DATABASE_URL env var for PostgreSQL in production
    DATABASE_URL: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL",
        description="Full database URL. Uses SQLite by default if not set.",
    )
    DATABASE_URL_SYNC: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL_SYNC",
        description="Sync database URL (used for alembic migrations).",
    )

    # PostgreSQL (only used if DATABASE_URL is explicitly set)
    POSTGRES_HOST: str = Field(default="localhost", alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="multimax", alias="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="multimax", alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="multimax_dev", alias="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Default to SQLite for zero-budget local development
        return "sqlite+aiosqlite:///./data/multimax.db"

    @property
    def database_url_sync(self) -> str:
        if self.DATABASE_URL_SYNC:
            return self.DATABASE_URL_SYNC
        if self.DATABASE_URL:
            # Build sync URL from async URL by removing +asyncpg
            return self.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
        return "sqlite:///./data/multimax.db"

    # --- ChromaDB ---
    CHROMADB_HOST: str = Field(default="localhost", alias="CHROMADB_HOST")
    CHROMADB_PORT: int = Field(default=8001, alias="CHROMADB_PORT")

    @property
    def chromadb_url(self) -> str:
        return f"http://{self.CHROMADB_HOST}:{self.CHROMADB_PORT}"

    # --- Ollama ---
    OLLAMA_HOST: str = Field(default="localhost", alias="OLLAMA_HOST")
    OLLAMA_PORT: int = Field(default=11434, alias="OLLAMA_PORT")
    OLLAMA_DEFAULT_MODEL: str = Field(default="phi3:latest", alias="OLLAMA_DEFAULT_MODEL")

    @property
    def ollama_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"

    # --- Storage ---
    UPLOAD_DIR: str = Field(default="./uploads", alias="UPLOAD_DIR")
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    STORAGE_BACKEND: str = Field(default="local", alias="STORAGE_BACKEND")

    # --- Supabase ---
    SUPABASE_URL: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_KEY")

    # --- Authentication ---
    AUTH_SECRET_KEY: str = Field(default="change-me-to-another-random-secret", alias="AUTH_SECRET_KEY")
    AUTH_ALGORITHM: str = Field(default="HS256", alias="AUTH_ALGORITHM")
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    AUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, alias="AUTH_REFRESH_TOKEN_EXPIRE_DAYS")
    AUTH_MAX_LOGIN_ATTEMPTS: int = Field(default=5, alias="AUTH_MAX_LOGIN_ATTEMPTS")
    AUTH_LOCKOUT_DURATION_MINUTES: int = Field(default=15, alias="AUTH_LOCKOUT_DURATION_MINUTES")

    # --- Event Bus ---
    EVENT_BUS_BACKEND: str = Field(default="memory", alias="EVENT_BUS_BACKEND")
    EVENT_BUS_MAX_RETRIES: int = Field(default=3, alias="EVENT_BUS_MAX_RETRIES")
    EVENT_BUS_RETRY_DELAY_SECONDS: int = Field(default=5, alias="EVENT_BUS_RETRY_DELAY_SECONDS")
    EVENT_BUS_DEAD_LETTER_MAX: int = Field(default=1000, alias="EVENT_BUS_DEAD_LETTER_MAX")

    # --- API ---
    API_RATE_LIMIT_PER_MINUTE: int = Field(default=60, alias="API_RATE_LIMIT_PER_MINUTE")
    API_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:3001",
        alias="API_CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.API_CORS_ORIGINS.split(",")]

    # --- Cloud AI Providers (optional) ---
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    CLAUDE_API_KEY: Optional[str] = Field(default=None, alias="CLAUDE_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance (singleton)."""
    return Settings()