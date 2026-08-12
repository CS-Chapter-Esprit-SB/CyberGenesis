"""Integration tests for the gateway JWT auth middleware."""

from __future__ import annotations

import json

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from server_by_auth import security
from server_by_auth.middleware import JWTAuthMiddleware, require_auth
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send


async def _identity_echo_app(scope: Scope, receive: Receive, send: Send) -> None:
    """Downstream app that echoes identity headers from the request scope."""
    headers = dict(scope.get("headers", []))
    body = json.dumps(
        {
            "user_id": headers.get(b"x-user-id", b"").decode(),
            "username": headers.get(b"x-username", b"").decode(),
        }
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send({"type": "http.response.body", "body": body})


@pytest.mark.asyncio
async def test_blocks_missing_token() -> None:
    app = JWTAuthMiddleware(JSONResponse({"ok": True}))
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/protected")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_blocks_invalid_token() -> None:
    app = JWTAuthMiddleware(JSONResponse({"ok": True}))
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/protected", headers={"Authorization": "Bearer garbage.token.here"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_allows_valid_token_and_injects_identity() -> None:
    token = security.create_access_token(7, "alice")
    app = JWTAuthMiddleware(_identity_echo_app)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "7"
    assert body["username"] == "alice"


@pytest.mark.asyncio
async def test_public_paths_are_allowed() -> None:
    app = JWTAuthMiddleware(JSONResponse({"ok": True}))
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/login")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_options_requests_are_allowed() -> None:
    app = JWTAuthMiddleware(JSONResponse({"ok": True}))
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request("OPTIONS", "/protected")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_require_auth_dependency() -> None:
    test_app = FastAPI()

    @test_app.get("/me")
    async def me(
        claims: dict[str, object] = Depends(require_auth),
    ) -> dict[str, object]:
        return {"sub": claims["sub"]}

    transport = ASGITransport(app=test_app)
    token = security.create_access_token(9, "bob")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        allowed = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
        blocked = await client.get("/me")

    assert allowed.status_code == 200
    assert allowed.json() == {"sub": "9"}
    assert blocked.status_code == 401
