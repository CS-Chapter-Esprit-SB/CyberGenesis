"""Unit tests for the Redis sliding-window rate limiter."""

from __future__ import annotations

import pytest
from fakeredis import FakeAsyncRedis
from server_by_rate_limiter.ratelimit import RedisSlidingWindowLimiter


@pytest.mark.asyncio
async def test_allows_requests_under_limit(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="ip", limit=3, window_ms=60_000
    )
    results = [
        await limiter.check("1.2.3.4", now_ms=1000 + index * 1000) for index in range(4)
    ]
    assert [result.allowed for result in results] == [True, True, True, False]
    assert results[0].remaining == 2
    assert results[2].remaining == 0
    assert results[3].remaining == 0


@pytest.mark.asyncio
async def test_identifiers_are_isolated(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="ip", limit=2, window_ms=60_000
    )
    first = await limiter.check("client-a", now_ms=1000)
    second = await limiter.check("client-b", now_ms=2000)
    assert first.allowed
    assert second.allowed


@pytest.mark.asyncio
async def test_window_slides(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="ip", limit=2, window_ms=60_000
    )
    now = 100_000
    await limiter.check("1.2.3.4", now_ms=now)
    await limiter.check("1.2.3.4", now_ms=now)
    denied = await limiter.check("1.2.3.4", now_ms=now + 1000)
    assert not denied.allowed

    allowed = await limiter.check("1.2.3.4", now_ms=now + 60_001)
    assert allowed.allowed


@pytest.mark.asyncio
async def test_reset_clears_state(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="token", limit=1, window_ms=60_000
    )
    await limiter.check("token-1", now_ms=1000)
    assert not (await limiter.check("token-1", now_ms=2000)).allowed

    await limiter.reset("token-1")
    assert (await limiter.check("token-1", now_ms=3000)).allowed


@pytest.mark.asyncio
async def test_reset_ms_tracks_oldest_request(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="ip", limit=2, window_ms=60_000
    )
    await limiter.check("1.2.3.4", now_ms=100_000)
    await limiter.check("1.2.3.4", now_ms=150_000)
    denied = await limiter.check("1.2.3.4", now_ms=150_001)
    assert not denied.allowed
    # Oldest entry (100_000) expires at 160_000 -> 9_999 ms left.
    assert denied.reset_ms == 9_999


@pytest.mark.asyncio
async def test_limit_scope_keys_are_namespaced(fake_redis: FakeAsyncRedis) -> None:
    limiter = RedisSlidingWindowLimiter(
        fake_redis, scope="token", limit=1, window_ms=60_000
    )
    await limiter.check("shared", now_ms=1000)
    assert not (await limiter.check("shared", now_ms=2000)).allowed

    other = RedisSlidingWindowLimiter(fake_redis, scope="ip", limit=1, window_ms=60_000)
    assert (await other.check("shared", now_ms=2000)).allowed
