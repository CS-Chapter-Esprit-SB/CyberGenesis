"""Tests for the URL Shortener Core Service HTTP client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from src.client_by_ahmed.url_shortener import URLShortenerClient

CREATE_PAYLOAD = {"id": 1, "code": "abc1234", "url": "https://example.com/foo"}


@pytest.mark.asyncio
async def test_create_url() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["json"] = json.loads(request.content)
        return httpx.Response(201, json=CREATE_PAYLOAD)

    transport = httpx.MockTransport(handler)
    async with URLShortenerClient(transport=transport) as client:
        payload = await client.create_url("https://example.com/foo")

    assert payload == CREATE_PAYLOAD
    assert seen["method"] == "POST"
    assert seen["url"].endswith("/urls")
    assert seen["json"] == {"url": "https://example.com/foo"}


@pytest.mark.asyncio
async def test_get_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert str(request.url).endswith("/urls/abc1234")
        return httpx.Response(200, json=CREATE_PAYLOAD)

    transport = httpx.MockTransport(handler)
    async with URLShortenerClient(transport=transport) as client:
        payload = await client.get_url("abc1234")

    assert payload == CREATE_PAYLOAD


@pytest.mark.asyncio
async def test_update_url() -> None:
    updated = {**CREATE_PAYLOAD, "url": "https://example.org/bar"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert str(request.url).endswith("/urls/abc1234")
        assert json.loads(request.content) == {"url": "https://example.org/bar"}
        return httpx.Response(200, json=updated)

    transport = httpx.MockTransport(handler)
    async with URLShortenerClient(transport=transport) as client:
        payload = await client.update_url("abc1234", "https://example.org/bar")

    assert payload == updated


@pytest.mark.asyncio
async def test_delete_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert str(request.url).endswith("/urls/abc1234")
        return httpx.Response(204)

    transport = httpx.MockTransport(handler)
    async with URLShortenerClient(transport=transport) as client:
        result = await client.delete_url("abc1234")

    assert result is None


@pytest.mark.asyncio
async def test_missing_url_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "URL not found"})

    transport = httpx.MockTransport(handler)
    async with URLShortenerClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_url("missing")
