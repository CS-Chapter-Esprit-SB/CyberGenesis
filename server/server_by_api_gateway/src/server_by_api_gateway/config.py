"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "API Gateway Service"
    host: str = "0.0.0.0"
    port: int = 8000

    auth_service_url: str = "http://localhost:8001"
    rate_limiter_service_url: str = "http://localhost:8002"
    url_shortener_service_url: str = "http://localhost:8000"

    retry_attempts: int = 5
    retry_wait_seconds: float = 0.1


settings = Settings()
