"""
config.py — Centralised settings via pydantic-settings.
All values are read from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    # Rate limiting
    rate_limit_max_requests: int = 10
    rate_limit_window_seconds: int = 60

    # LLM
    llm_provider: str = "stub"   # "stub" | "anthropic" | "openai" | "google"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Database (SQLite for dev, PostgreSQL for prod)
    database_url: str = "sqlite+aiosqlite:///./coach.db"

    # Qdrant vector DB (empty = in-memory, no server needed)
    qdrant_url: str = ""


# Singleton — import this everywhere
settings = Settings()
