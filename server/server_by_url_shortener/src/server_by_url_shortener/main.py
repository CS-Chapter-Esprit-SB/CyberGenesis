"""FastAPI application entrypoint for the URL shortener service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from server_by_url_shortener.api.routes import router
from server_by_url_shortener.config import settings
from server_by_url_shortener.crud import ShortCodeExhaustedError
from server_by_url_shortener.db import init_db


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

    @application.exception_handler(ShortCodeExhaustedError)
    async def short_code_exhausted_handler(
        request: Request, exc: ShortCodeExhaustedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "could not allocate a unique short code"},
        )

    return application


app = create_app()


def run() -> None:
    """Run the service with uvicorn (console script entrypoint)."""
    import uvicorn

    uvicorn.run(
        "server_by_url_shortener.main:app",
        host=settings.host,
        port=settings.port,
    )
