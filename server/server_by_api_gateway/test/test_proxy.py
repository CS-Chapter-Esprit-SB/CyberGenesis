"""Unit tests for the gateway retryable reverse-proxy client."""

from __future__ import annotations

import logging

import httpx
import pytest
from server_by_api_gateway.proxy import TRANSIENT_STATUS_CODES, forward

TARGET = "http://downstream:8000/api/v1/echo"


class RecordingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.mark.asyncio
async def test_returns_success_without_retry() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        response = await forward(
            client,
            "GET",
            TARGET,
            {},
            b"",
            retry_attempts=5,
            wait_seconds=0.001,
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_retries_transient_503_then_succeeds() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, content=b"busy")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        response = await forward(
            client,
            "GET",
            TARGET,
            {},
            b"",
            retry_attempts=5,
            wait_seconds=0.001,
        )

    assert response.status_code == 200
    assert calls == 2


@pytest.mark.asyncio
async def test_retries_each_transient_status() -> None:
    for status in sorted(TRANSIENT_STATUS_CODES):
        calls = 0

        async def handler(
            request: httpx.Request, status: int = status
        ) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(status, content=b"busy")
            return httpx.Response(200, json={"ok": True})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await forward(
                client,
                "GET",
                TARGET,
                {},
                b"",
                retry_attempts=5,
                wait_seconds=0.001,
            )

        assert response.status_code == 200, f"status {status} should be retried"


@pytest.mark.asyncio
async def test_does_not_retry_non_transient_5xx() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, content=b"boom")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        response = await forward(
            client,
            "GET",
            TARGET,
            {},
            b"",
            retry_attempts=5,
            wait_seconds=0.001,
        )

    assert response.status_code == 500
    assert calls == 1


@pytest.mark.asyncio
async def test_returns_502_and_logs_error_after_exhausting_retries() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, content=b"busy")

    logger = logging.getLogger("server_by_api_gateway.proxy")
    recorder = RecordingHandler()
    logger.addHandler(recorder)
    try:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await forward(
                client,
                "GET",
                TARGET,
                {},
                b"",
                retry_attempts=3,
                wait_seconds=0.001,
            )
    finally:
        logger.removeHandler(recorder)

    assert response.status_code == 502
    assert calls == 4
    assert any(
        record.levelname == "ERROR"
        and record.getMessage() == "downstream request failed"
        for record in recorder.records
    )


@pytest.mark.asyncio
async def test_returns_502_when_downstream_unreachable() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        response = await forward(
            client,
            "GET",
            TARGET,
            {},
            b"",
            retry_attempts=2,
            wait_seconds=0.001,
        )

    assert response.status_code == 502
