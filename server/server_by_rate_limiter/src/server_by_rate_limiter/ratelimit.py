"""Sliding-window rate limiting over Redis sorted sets.

Each request is recorded as a member of a sorted set keyed by
``rl:{scope}:{identifier}`` with its arrival timestamp as the score. Every
check atomically (via a MULTI/EXEC pipeline) prunes entries that fell outside
the window, records the current request, refreshes the key TTL and returns the
resulting count. A request is allowed while the count stays within the limit.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import uuid4

from redis.asyncio import Redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_ms: int

    def reset_seconds(self) -> int:
        """Whole seconds until the client regains capacity (min 1)."""
        return max(1, round(self.reset_ms / 1000))


class RedisSlidingWindowLimiter:
    def __init__(
        self,
        client: Redis,
        scope: str,
        limit: int,
        window_ms: int,
        key_prefix: str = "rl",
    ) -> None:
        self._client = client
        self.scope = scope
        self.limit = limit
        self._window_ms = window_ms
        self._key_prefix = key_prefix

    def _key(self, identifier: str) -> str:
        return f"{self._key_prefix}:{self.scope}:{identifier}"

    async def check(
        self, identifier: str, now_ms: int | None = None
    ) -> RateLimitResult:
        """Record a request and report whether it stays within the limit."""
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        key = self._key(identifier)

        async with self._client.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, now - self._window_ms)
            pipe.zadd(key, {f"{now}:{uuid4().hex}": now})
            pipe.pexpire(key, self._window_ms)
            pipe.zcard(key)
            results = await pipe.execute()

        count = int(results[3])
        remaining = max(0, self.limit - count)
        reset_ms = await self._reset_ms(key, now)
        return RateLimitResult(
            allowed=count <= self.limit,
            limit=self.limit,
            remaining=remaining,
            reset_ms=reset_ms,
        )

    async def reset(self, identifier: str) -> None:
        """Clear all recorded requests for an identifier."""
        await self._client.delete(self._key(identifier))

    async def _reset_ms(self, key: str, now_ms: int) -> int:
        members = await self._client.zrange(key, 0, 0, withscores=True)
        if not members:
            return self._window_ms
        oldest_ms = int(members[0][1])
        return max(0, self._window_ms - (now_ms - oldest_ms))
