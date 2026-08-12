"""ASGI middleware intercepting requests at the gateway level.

Enforces a configured sliding-window limit keyed by client IP or bearer token.
Denied requests receive ``429 Too Many Requests`` with standard rate-limit
header metadata, and a warning is emitted through the structured logger.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from server_by_rate_limiter.ratelimit import RateLimitResult, RedisSlidingWindowLimiter
from server_by_rate_limiter.structured_logger import get_logger

logger = get_logger("server_by_rate_limiter.middleware")


def client_ip(request: Request) -> str:
    """Best-effort client IP using X-Forwarded-For, falling back to the peer."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


def bearer_token(request: Request) -> str | None:
    """Bearer token from the Authorization header, or None when absent."""
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def gateway_identifier(request: Request) -> str | None:
    """Rate-limit by bearer token when present, otherwise by client IP."""
    token = bearer_token(request)
    if token:
        return token
    return client_ip(request)


IdentifierGetter = Callable[[Request], str | None]


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        limiter: RedisSlidingWindowLimiter,
        get_identifier: IdentifierGetter,
    ) -> None:
        self.app = app
        self._limiter = limiter
        self._get_identifier = get_identifier

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        identifier = self._get_identifier(request)
        if identifier is None:
            await self.app(scope, receive, send)
            return

        result = await self._limiter.check(identifier)
        if not result.allowed:
            logger.warning(
                "rate limit exceeded",
                extra={
                    "scope": self._limiter.scope,
                    "identifier": identifier,
                    "limit": self._limiter.limit,
                },
            )
            await self._send_429(result, scope, receive, send)
            return

        await self.app(scope, receive, self._with_headers(send, result))

    async def _send_429(
        self, result: RateLimitResult, scope: Scope, receive: Receive, send: Send
    ) -> None:
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + result.reset_seconds()),
            "Retry-After": str(result.reset_seconds()),
        }
        response = JSONResponse(
            {"detail": "Too Many Requests"},
            status_code=429,
            headers=headers,
        )
        await response(scope, receive, send)

    def _with_headers(
        self, send: Send, result: RateLimitResult
    ) -> Callable[[dict[str, Any]], Awaitable[None]]:
        extra = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(time.time()) + result.reset_seconds()),
        }

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).update(extra)
            await send(message)

        return send_wrapper
