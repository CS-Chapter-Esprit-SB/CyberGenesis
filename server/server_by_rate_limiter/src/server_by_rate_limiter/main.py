"""FastAPI application entrypoint for the rate limiter service.

Mounts the gateway rate-limit middleware in front of the sample routes. The
middleware classes are reusable and can be dropped into any gateway ASGI app.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from server_by_rate_limiter.config import settings
from server_by_rate_limiter.middleware import RateLimitMiddleware, gateway_identifier
from server_by_rate_limiter.ratelimit import RedisSlidingWindowLimiter
from server_by_rate_limiter.redis_client import close_redis, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_redis()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/echo", tags=["demo"])
    async def echo() -> dict[str, str]:
        return {"message": "pong"}

    limiter = RedisSlidingWindowLimiter(
        redis_client,
        scope="gateway",
        limit=settings.default_limit,
        window_ms=settings.default_window_ms,
    )
    application.add_middleware(
        RateLimitMiddleware, limiter=limiter, get_identifier=gateway_identifier
    )

    return application


app = create_app()


def run() -> None:
    """Run the service with uvicorn (console script entrypoint)."""
    import uvicorn

    uvicorn.run(
        "server_by_rate_limiter.main:app",
        host=settings.host,
        port=settings.port,
    )
