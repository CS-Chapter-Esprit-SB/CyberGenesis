"""Configuration for the API Gateway, loaded from environment variables."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DownstreamService:
    name: str
    base_url: str


@dataclass(frozen=True)
class GatewaySettings:
    host: str = field(default_factory=lambda: os.getenv("GATEWAY_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("GATEWAY_PORT", "8000")))

    retry_attempts: int = field(
        default_factory=lambda: int(os.getenv("RETRY_ATTEMPTS", "5"))
    )
    retry_wait_seconds: float = field(
        default_factory=lambda: float(os.getenv("RETRY_WAIT_SECONDS", "1.0"))
    )
    downstream_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5.0"))
    )

    auth_service_url: str = field(
        default_factory=lambda: os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    )
    rate_limiter_service_url: str = field(
        default_factory=lambda: os.getenv(
            "RATE_LIMITER_SERVICE_URL", "http://localhost:8002"
        )
    )
    url_shortener_service_url: str = field(
        default_factory=lambda: os.getenv(
            "URL_SHORTENER_SERVICE_URL", "http://localhost:8003"
        )
    )

    @property
    def downstream_services(self) -> dict[str, DownstreamService]:
        return {
            "auth": DownstreamService("auth", self.auth_service_url),
            "rate-limiter": DownstreamService(
                "rate-limiter", self.rate_limiter_service_url
            ),
            "url-shortener": DownstreamService(
                "url-shortener", self.url_shortener_service_url
            ),
        }


settings = GatewaySettings()
