"""Integration tests for the gateway rate-limit middleware."""

from __future__ import annotations

import logging

import pytest
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient
from server_by_rate_limiter.config import settings
from server_by_rate_limiter.middleware import (
    RateLimitMiddleware,
    bearer_token,
    client_ip,
    gateway_identifier,
)
from server_by_rate_limiter.ratelimit import RedisSlidingWindowLimiter
from starlette.responses import JSONResponse


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.asyncio
async def test_returns_429_with_standard_headers(
    fake_redis: FakeAsyncRedis,
) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="ip", limit=2, window_ms=60_000
    )
    middleware = RateLimitMiddleware(JSONResponse({"ok": True}), limiter, client_ip)
    transport = ASGITransport(app=middleware)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get("/")
        second = await client.get("/")
        third = await client.get("/")

    assert first.status_code == 200
    assert first.headers["x-ratelimit-limit"] == "2"
    assert first.headers["x-ratelimit-remaining"] == "1"

    assert second.status_code == 200

    assert third.status_code == 429
    assert third.json()["detail"] == "Too Many Requests"
    assert third.headers["x-ratelimit-limit"] == "2"
    assert third.headers["x-ratelimit-remaining"] == "0"
    assert third.headers["x-ratelimit-reset"]
    assert int(third.headers["retry-after"]) >= 1


@pytest.mark.asyncio
async def test_emits_warning_on_rate_limit_trigger(
    fake_redis: FakeAsyncRedis,
) -> None:
    logger = logging.getLogger("server_by_rate_limiter.middleware")
    handler = CaptureHandler()
    logger.addHandler(handler)
    try:
        limiter = RedisSlidingWindowLimiter(
            fake_redis, scope="ip", limit=1, window_ms=60_000
        )
        middleware = RateLimitMiddleware(JSONResponse({"ok": True}), limiter, client_ip)
        transport = ASGITransport(app=middleware)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/")
            await client.get("/")

        assert len(handler.records) == 1
        record = handler.records[0]
        assert record.levelno == logging.WARNING
        assert record.scope == "ip"
        assert record.identifier
        assert record.limit == 1
    finally:
        logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_token_based_limiting(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="token", limit=1, window_ms=60_000
    )
    middleware = RateLimitMiddleware(JSONResponse({"ok": True}), limiter, bearer_token)
    transport = ASGITransport(app=middleware)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        allowed = await client.get("/", headers={"Authorization": "Bearer tok123"})
        denied = await client.get("/", headers={"Authorization": "Bearer tok123"})
        other = await client.get("/", headers={"Authorization": "Bearer other-token"})

    assert allowed.status_code == 200
    assert denied.status_code == 429
    assert other.status_code == 200


@pytest.mark.asyncio
async def test_missing_identifier_passes_through(
    fake_redis: FakeAsyncRedis,
) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="token", limit=1, window_ms=60_000
    )
    middleware = RateLimitMiddleware(JSONResponse({"ok": True}), limiter, bearer_token)
    transport = ASGITransport(app=middleware)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_gateway_identifier_prefers_token(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="gateway", limit=1, window_ms=60_000
    )
    middleware = RateLimitMiddleware(
        JSONResponse({"ok": True}), limiter, gateway_identifier
    )
    transport = ASGITransport(app=middleware)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ip_allowed = await client.get("/")
        ip_denied = await client.get("/")
        token_allowed = await client.get(
            "/", headers={"Authorization": "Bearer separate-token"}
        )

    assert ip_allowed.status_code == 200
    assert ip_denied.status_code == 429
    assert token_allowed.status_code == 200


class _StubJWTAuthMiddleware:
    """Minimal ASGI JWT gate for gateway stack-order tests."""

    def __init__(
        self,
        app,
        *,
        token: str,
        user_id: str,
        username: str,
    ) -> None:
        self.app = app
        self._token = token
        self._user_id = user_id
        self._username = username

    async def __call__(self, scope, receive, send) -> None:
        from starlette.requests import Request

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            response = JSONResponse(
                {"detail": "authentication required"}, status_code=401
            )
            await response(scope, receive, send)
            return
        if header[7:].strip() != self._token:
            response = JSONResponse(
                {"detail": "authentication required"}, status_code=401
            )
            await response(scope, receive, send)
            return
        headers = list(scope.get("headers", []))
        headers.append((b"x-user-id", self._user_id.encode()))
        headers.append((b"x-username", self._username.encode()))
        await self.app({**scope, "headers": headers}, receive, send)


@pytest.mark.asyncio
async def test_gateway_stack_rate_limit_before_auth(
    fake_redis: FakeAsyncRedis,
) -> None:
    """Rate limiting runs before JWT auth at the gateway edge."""
    import json

    from starlette.types import Receive, Scope, Send

    async def identity_echo_app(scope: Scope, receive: Receive, send: Send) -> None:
        headers = dict(scope.get("headers", []))
        body = json.dumps(
            {
                "user_id": headers.get(b"x-user-id", b"").decode(),
                "username": headers.get(b"x-username", b"").decode(),
            }
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            }
        )
        await send({"type": "http.response.body", "body": body})

    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="gateway", limit=1, window_ms=60_000
    )
    gateway_token = "gateway-test-token"
    downstream = _StubJWTAuthMiddleware(
        identity_echo_app,
        token=gateway_token,
        user_id="3",
        username="gateway-user",
    )
    gateway = RateLimitMiddleware(downstream, limiter, gateway_identifier)
    transport = ASGITransport(app=gateway)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get(
            "/protected", headers={"Authorization": f"Bearer {gateway_token}"}
        )
        second = await client.get(
            "/protected", headers={"Authorization": f"Bearer {gateway_token}"}
        )

    assert first.status_code == 200
    assert first.json() == {"user_id": "3", "username": "gateway-user"}
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_fastapi_app_enforces_limit(
    fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    import server_by_rate_limiter.main as main

    monkeypatch.setattr(main, "redis_client", fake_redis)
    application = main.create_app()
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(settings.default_limit):
            response = await client.get("/echo")
        denied = await client.get("/echo")

    assert response.status_code == 200
    assert denied.status_code == 429
