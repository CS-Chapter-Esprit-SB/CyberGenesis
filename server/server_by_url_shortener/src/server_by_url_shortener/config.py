"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "URL Shortener Service"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "postgresql+asyncpg://cybergen:cybergen@localhost:5432/cybergen"


settings = Settings()
