import logging

import fakeredis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from server_example.gateway import RateLimitMiddleware
from server_example.rate_limiter import SlidingWindowRateLimiter
from server_example.structured_logger import StructuredLogger


def test_sliding_window_rate_limiter_blocks_when_limit_exceeded() -> None:
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    limiter = SlidingWindowRateLimiter(
        redis_client=redis_client,
        limit=2,
        window_seconds=60,
        prefix="demo",
    )

    allowed_first, meta_first = limiter.allow("client-123")
    allowed_second, meta_second = limiter.allow("client-123")
    allowed_third, meta_third = limiter.allow("client-123")

    assert allowed_first is True
    assert allowed_second is True
    assert allowed_third is False
    assert meta_first["limit"] == 2
    assert meta_third["limit"] == 2
    assert meta_third["retry_after"] >= 0


def test_gateway_returns_http_429_and_logs_warning() -> None:
    app = FastAPI()
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    logger = StructuredLogger("gateway")

    @app.middleware("http")
    async def gateway_middleware(request, call_next):
        return await RateLimitMiddleware(
            app,
            redis_client=redis_client,
            limit=1,
            window_seconds=60,
            logger=logger,
            lookup_keys=("ip", "token"),
        ).dispatch(request, call_next)

    @app.get("/resource")
    async def resource() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    first = client.get("/resource", headers={"X-Forwarded-For": "203.0.113.10"})
    second = client.get("/resource", headers={"X-Forwarded-For": "203.0.113.10"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"]
    assert second.headers["X-RateLimit-Limit"] == "1"

    record = next(
        entry
        for entry in logger.logger.handlers[0].records
        if entry.levelno == logging.WARNING
    )
    assert "rate_limit_triggered" in record.getMessage()
