"""FastAPI application entrypoint for the auth service.

``create_gateway_app`` demonstrates how the ``JWTAuthMiddleware`` can be
mounted at the gateway level in front of any downstream ASGI app to block
unauthenticated requests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.types import ASGIApp

from server_by_auth.api.routes import router
from server_by_auth.config import settings
from server_by_auth.db import init_db
from server_by_auth.middleware import JWTAuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(router)

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


def create_gateway_app(downstream: ASGIApp) -> ASGIApp:
    """Wrap a downstream app with gateway JWT authentication."""
    return JWTAuthMiddleware(downstream)


app = create_app()


def run() -> None:
    """Run the service with uvicorn (console script entrypoint)."""
    import uvicorn

    uvicorn.run(
        "server_by_auth.main:app",
        host=settings.host,
        port=settings.port,
    )
