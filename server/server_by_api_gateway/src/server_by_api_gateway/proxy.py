"""Async reverse-proxy client with bounded retry for downstream failures.

A single logical request is retried up to ``retry_attempts`` times, waiting
``wait_seconds`` between attempts, when the downstream service responds with
a transient 5xx status (502, 503, 504) or the connection itself fails. Once
the budget is exhausted the failure is logged through the structured logger
at ERROR level and a ``502 Bad Gateway`` response is returned.
"""

from __future__ import annotations

import asyncio
import json

import httpx

from server_by_api_gateway.structured_logger import get_logger

logger = get_logger("server_by_api_gateway.proxy")

TRANSIENT_STATUS_CODES = frozenset({502, 503, 504})

RESPONSE_HEADERS_TO_DROP = frozenset(
    {"content-length", "transfer-encoding", "connection", "keep-alive"}
)

REQUEST_HEADERS_TO_DROP = frozenset(
    {"host", "content-length", "connection", "keep-alive", "transfer-encoding"}
)


async def forward(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict[str, str],
    content: bytes,
    *,
    retry_attempts: int,
    wait_seconds: float,
) -> httpx.Response:
    """Proxy a request to ``url`` retrying transient failures."""
    last_error: httpx.HTTPError | None = None
    last_response: httpx.Response | None = None
    for attempt in range(retry_attempts + 1):
        try:
            response = await client.request(
                method, url, headers=headers, content=content
            )
        except httpx.HTTPError as exc:
            last_error = exc
            last_response = None
            if attempt >= retry_attempts:
                break
            await asyncio.sleep(wait_seconds)
            continue

        last_response = response
        if response.status_code not in TRANSIENT_STATUS_CODES:
            return response
        if attempt >= retry_attempts:
            break
        await asyncio.sleep(wait_seconds)

    return _failure_response(method, url, last_error, last_response)


def _failure_response(
    method: str,
    url: str,
    error: httpx.HTTPError | None,
    response: httpx.Response | None,
) -> httpx.Response:
    extra: dict[str, object] = {"method": method, "url": url}
    if error is not None:
        extra["error"] = repr(error)
    if response is not None:
        extra["status_code"] = response.status_code
    logger.error("downstream request failed", extra=extra)
    return httpx.Response(
        status_code=502,
        content=json.dumps({"detail": "Bad Gateway"}).encode("utf-8"),
        headers={"content-type": "application/json"},
    )


def filter_request_headers(headers: dict[str, str]) -> dict[str, str]:
    """Drop hop-by-hop headers before forwarding upstream."""
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in REQUEST_HEADERS_TO_DROP
    }


def filter_response_headers(headers: httpx.Headers) -> dict[str, str]:
    """Drop hop-by-hop headers before returning the downstream response."""
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in RESPONSE_HEADERS_TO_DROP
    }
