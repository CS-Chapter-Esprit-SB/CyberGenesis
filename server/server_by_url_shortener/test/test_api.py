"""Integration tests for the URL shortener CRUD API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from server_by_url_shortener import crud
from server_by_url_shortener.shortcode import ALPHABET

VALID_URL = "https://example.com/foo"
OTHER_URL = "https://example.org/bar"


async def create_url(client: AsyncClient, url: str = VALID_URL) -> dict:
    response = await client.post("/urls", json={"url": url})
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_url(client: AsyncClient) -> None:
    payload = await create_url(client)
    assert payload["url"] == VALID_URL
    assert len(payload["code"]) == 7
    assert all(char in ALPHABET for char in payload["code"])
    assert payload["id"] > 0
    assert "created_at" in payload
    assert "updated_at" in payload


@pytest.mark.asyncio
async def test_create_url_rejects_invalid_url(client: AsyncClient) -> None:
    response = await client.post("/urls", json={"url": "not-a-url"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_urls_generate_unique_codes(client: AsyncClient) -> None:
    codes = set()
    for index in range(20):
        payload = await create_url(client, f"https://example.com/{index}")
        codes.add(payload["code"])
    assert len(codes) == 20


@pytest.mark.asyncio
async def test_get_url(client: AsyncClient) -> None:
    created = await create_url(client)
    response = await client.get(f"/urls/{created['code']}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == created["code"]
    assert body["url"] == VALID_URL


@pytest.mark.asyncio
async def test_get_missing_url_returns_404(client: AsyncClient) -> None:
    response = await client.get("/urls/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_url(client: AsyncClient) -> None:
    created = await create_url(client)
    response = await client.put(f"/urls/{created['code']}", json={"url": OTHER_URL})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == created["code"]
    assert body["url"] == OTHER_URL


@pytest.mark.asyncio
async def test_update_missing_url_returns_404(client: AsyncClient) -> None:
    response = await client.put("/urls/nonexistent", json={"url": OTHER_URL})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_url(client: AsyncClient) -> None:
    created = await create_url(client)
    response = await client.delete(f"/urls/{created['code']}")
    assert response.status_code == 204
    missing = await client.get(f"/urls/{created['code']}")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_delete_missing_url_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/urls/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_url_retries_on_code_collision(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    occupied = (await create_url(client))["code"]
    codes = iter([occupied, "FreshCode"])
    monkeypatch.setattr(crud, "generate_short_code", lambda: next(codes))

    response = await client.post("/urls", json={"url": OTHER_URL})
    assert response.status_code == 201
    assert response.json()["code"] == "FreshCode"


@pytest.mark.asyncio
async def test_create_url_exhausts_code_retries(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    occupied = (await create_url(client))["code"]
    monkeypatch.setattr(crud, "generate_short_code", lambda: occupied)

    response = await client.post("/urls", json={"url": OTHER_URL})
    assert response.status_code == 500
