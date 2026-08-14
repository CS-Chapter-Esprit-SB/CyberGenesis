from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .rate_limiter import SlidingWindowRateLimiter
from .structured_logger import StructuredLogger


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        redis_client: Any,
        limit: int,
        window_seconds: int,
        logger: StructuredLogger | None = None,
        prefix: str = "gateway_rate_limit",
        lookup_keys: tuple[str, ...] = ("ip", "token"),
    ) -> None:
        self.app = app
        self.rate_limiter = SlidingWindowRateLimiter(
            redis_client=redis_client,
            limit=limit,
            window_seconds=window_seconds,
            prefix=prefix,
        )
        self.logger = logger or StructuredLogger("gateway")
        self.limit = limit
        self.window_seconds = window_seconds
        self.lookup_keys = lookup_keys
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Any]],
    ) -> Any:
        client_id = self._resolve_client_id(request)
        allowed, metadata = self.rate_limiter.allow(client_id)

        if not allowed:
            retry_after = int(metadata.get("retry_after", 0))
            reset_epoch = int(time.time() + retry_after)
            headers = {
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(self.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_epoch),
            }
            self.logger.warning(
                "rate_limit_triggered",
                client_id=client_id,
                limit=self.limit,
                window_seconds=self.window_seconds,
                method=request.method,
                path=request.url.path,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers=headers,
            )

        response = await call_next(request)
        remaining = int(metadata.get("remaining", 0))
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + self.window_seconds)
        )
        return response

    def _resolve_client_id(self, request: Request) -> str:
        parts: list[str] = []

        if "ip" in self.lookup_keys:
            forwarded = request.headers.get("x-forwarded-for")
            client_host = request.client.host if request.client else "unknown"
            parts.append(forwarded.split(",")[0].strip() if forwarded else client_host)

        if "token" in self.lookup_keys:
            token = (
                request.headers.get("authorization")
                or request.headers.get("x-api-key")
                or request.headers.get("token")
                or "anonymous"
            )
            parts.append(token)

        return "|".join(parts) if parts else "anonymous"
