from __future__ import annotations

import time
from typing import Any


class SlidingWindowRateLimiter:
    _RATE_LIMIT_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window_start = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    local request_id = ARGV[4]
    local window_seconds = tonumber(ARGV[5])

    redis.call("ZREMRANGEBYSCORE", key, 0, window_start)

    local current_count = redis.call("ZCARD", key)

    if current_count >= limit then
        local earliest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")

        if #earliest >= 2 then
            local oldest_timestamp = tonumber(earliest[2])

            if oldest_timestamp then
                local retry_after = math.ceil(
                    (oldest_timestamp + window_seconds) - now
                )

                if retry_after < 1 then
                    retry_after = 1
                end

                return {
                    0,
                    current_count,
                    retry_after
                }
            end
        end

        return {
            0,
            current_count,
            1
        }
    end

    redis.call("ZADD", key, now, request_id)
    redis.call("EXPIRE", key, window_seconds + 1)

    return {
        1,
        current_count + 1,
        0
    }
    """

    def __init__(
        self,
        redis_client: Any,
        limit: int,
        window_seconds: int,
        prefix: str = "gateway_rate_limit",
    ) -> None:
        self.redis = redis_client
        self.limit = int(limit)
        self.window_seconds = int(window_seconds)
        self.prefix = prefix

    def _key(self, identifier: str) -> str:
        return f"{self.prefix}:{identifier}"

    def allow(self, client_id: str) -> tuple[bool, dict[str, Any]]:
        now = time.time()
        key = self._key(client_id)
        request_id = f"{now}:{time.monotonic_ns()}"

        window_start = now - self.window_seconds

        result = self.redis.eval(
            self._RATE_LIMIT_SCRIPT,
            1,
            key,
            now,
            window_start,
            self.limit,
            request_id,
            self.window_seconds,
        )

        allowed = bool(int(result[0]))
        current_count = int(result[1])
        retry_after = int(result[2])

        if not allowed:
            return False, {
                "allowed": False,
                "limit": self.limit,
                "window_seconds": self.window_seconds,
                "remaining": 0,
                "retry_after": retry_after,
            }

        return True, {
            "allowed": True,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "remaining": max(0, self.limit - current_count),
            "retry_after": 0,
        }
