"""HTTP client for the URL Shortener Core Service API.

Wraps ``httpx.AsyncClient`` and exposes typed methods for every CRUD
endpoint of ``server_by_url_shortener`` (``POST /urls``, ``GET /urls/{code}``,
``PUT /urls/{code}``, ``DELETE /urls/{code}``).
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


class URLShortenerClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            transport=transport,
        )

    async def create_url(self, url: str) -> dict[str, Any]:
        response = await self._client.post("/urls", json={"url": url})
        response.raise_for_status()
        return response.json()

    async def get_url(self, code: str) -> dict[str, Any]:
        response = await self._client.get(f"/urls/{code}")
        response.raise_for_status()
        return response.json()

    async def update_url(self, code: str, url: str) -> dict[str, Any]:
        response = await self._client.put(f"/urls/{code}", json={"url": url})
        response.raise_for_status()
        return response.json()

    async def delete_url(self, code: str) -> None:
        response = await self._client.delete(f"/urls/{code}")
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> URLShortenerClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
