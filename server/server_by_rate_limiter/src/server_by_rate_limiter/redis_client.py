"""Async Redis client for the rate limiter service."""

from __future__ import annotations

import redis.asyncio as aioredis

from server_by_rate_limiter.config import settings

redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    await redis_client.aclose()
