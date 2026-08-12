"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Auth Service"
    host: str = "0.0.0.0"
    port: int = 8001
    database_url: str = "postgresql+asyncpg://cybergen:cybergen@localhost:5432/cybergen"
    jwt_secret: str = "dev-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "cybergen-auth"
    access_token_expire_minutes: int = 30


settings = Settings()
