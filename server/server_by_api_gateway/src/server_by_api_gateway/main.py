"""FastAPI application entrypoint for the API Gateway service.

The gateway routes client requests to downstream microservices (Auth, Rate
Limiter, URL Shortener) based on path prefixes, applying bounded retries with
a fixed wait time to transient downstream failures and logging them via the
structured logger at ERROR level.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

from server_by_api_gateway.config import settings
from server_by_api_gateway.proxy import (
    filter_request_headers,
    filter_response_headers,
    forward,
)
from server_by_api_gateway.routing import ROUTES, Route, target_for

_ALL_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.transport_client.aclose()


def create_app(transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    client = httpx.AsyncClient(transport=transport)
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.transport_client = client

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    for route in ROUTES:
        _register_route(application, client, route)

    return application


def _register_route(
    application: FastAPI, client: httpx.AsyncClient, route: Route
) -> None:
    prefix = route.prefix

    async def proxied(request: Request) -> Response:
        return await _proxy(client, request)

    application.add_api_route(
        f"{prefix}/{{path:path}}",
        proxied,
        methods=_ALL_METHODS,
        include_in_schema=False,
    )
    application.add_api_route(
        prefix,
        proxied,
        methods=_ALL_METHODS,
        include_in_schema=False,
    )


async def _proxy(client: httpx.AsyncClient, request: Request) -> Response:
    matched = target_for(request.url.path)
    if matched is None:
        return Response(status_code=404, content=b"Not Found")

    route, path = matched
    target_url = route.target.rstrip("/") + path
    query = request.url.query
    if query:
        target_url = f"{target_url}?{query}"

    body = await request.body()
    downstream = await forward(
        client,
        request.method,
        target_url,
        filter_request_headers(dict(request.headers)),
        body,
        retry_attempts=settings.retry_attempts,
        wait_seconds=settings.retry_wait_seconds,
    )
    return Response(
        status_code=downstream.status_code,
        content=downstream.content,
        headers=filter_response_headers(downstream.headers),
    )


app = create_app()


def run() -> None:
    """Run the service with uvicorn (console script entrypoint)."""
    import uvicorn

    uvicorn.run(
        "server_by_api_gateway.main:app",
        host=settings.host,
        port=settings.port,
    )
