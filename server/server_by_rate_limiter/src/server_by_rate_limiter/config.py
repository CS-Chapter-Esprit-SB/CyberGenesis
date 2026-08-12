"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Rate Limiter Service"
    host: str = "0.0.0.0"
    port: int = 8002
    redis_url: str = "redis://localhost:6379/0"
    default_limit: int = 100
    default_window_ms: int = 60_000


settings = Settings()
