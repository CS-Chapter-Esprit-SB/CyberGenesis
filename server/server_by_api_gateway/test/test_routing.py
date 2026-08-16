"""Integration tests for gateway routing to downstream microservices."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from server_by_api_gateway.main import create_app


def _unexpected_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(500, content=b"unexpected downstream call")


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    app = create_app(transport=httpx.MockTransport(_unexpected_handler))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_routes_to_auth_service() -> None:
    requests: list[Any] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, str(request.url), request.content))
        return httpx.Response(200, json={"token_type": "bearer"})

    app = create_app(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": "secret"},
        )

    assert response.status_code == 200
    assert response.json() == {"token_type": "bearer"}
    method, url, body = requests[0]
    assert method == "POST"
    assert url == "http://localhost:8001/api/v1/auth/login"
    assert b'"username":"alice"' in body


@pytest.mark.asyncio
async def test_routes_to_rate_limiter_stripping_prefix() -> None:
    requests: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, json={"message": "pong"})

    app = create_app(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/ratelimit/echo")

    assert response.status_code == 200
    assert requests == ["http://localhost:8002/echo"]


@pytest.mark.asyncio
async def test_routes_to_url_shortener_preserving_path() -> None:
    requests: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, json={"code": "abc123"})

    app = create_app(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/urls/abc123")

    assert response.status_code == 200
    assert requests == ["http://localhost:8000/urls/abc123"]


@pytest.mark.asyncio
async def test_forwards_query_string() -> None:
    requests: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, json={})

    app = create_app(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/api/v1/auth/verify?token=abc")

    assert requests == ["http://localhost:8001/api/v1/auth/verify?token=abc"]


@pytest.mark.asyncio
async def test_returns_404_for_unrouted_path() -> None:
    app = create_app(transport=httpx.MockTransport(_unexpected_handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/unknown/route")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_gateway_recovers_after_transient_downstream_failure() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, content=b"busy")
        return httpx.Response(200, json={"code": "abc123"})

    app = create_app(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/urls/abc123")

    assert response.status_code == 200
    assert calls == 2


@pytest.mark.asyncio
async def test_gateway_returns_502_after_exhausted_retries() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, content=b"busy")

    app = create_app(transport=httpx.MockTransport(handler))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/urls/abc123")

    assert response.status_code == 502
    assert calls == 6
