"""Integration tests for the auth API endpoints."""

from __future__ import annotations

from httpx import AsyncClient
from server_by_auth import security
from server_by_auth.config import settings

USERNAME = "alice"
PASSWORD = "password123"


async def register(
    client: AsyncClient, username: str = USERNAME, password: str = PASSWORD
) -> object:
    return await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )


async def login(
    client: AsyncClient, username: str = USERNAME, password: str = PASSWORD
) -> object:
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


async def test_register_creates_user(client: AsyncClient) -> None:
    response = await register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == USERNAME
    assert body["id"] > 0
    assert "password_hash" not in body


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"username": "bob", "password": "short"}
    )
    assert response.status_code == 422


async def test_register_duplicate_username(client: AsyncClient) -> None:
    await register(client)
    response = await register(client)
    assert response.status_code == 409


async def test_login_issues_jwt(client: AsyncClient) -> None:
    await register(client)
    response = await login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.access_token_expire_minutes * 60

    claims = security.decode_token(body["access_token"])
    assert claims["username"] == USERNAME


async def test_login_wrong_password(client: AsyncClient) -> None:
    await register(client)
    response = await login(client, password="wrong-password")
    assert response.status_code == 401


async def test_login_unknown_user(client: AsyncClient) -> None:
    response = await login(client, username="nobody")
    assert response.status_code == 401


async def test_verify_valid_token(client: AsyncClient) -> None:
    await register(client)
    login_response = await login(client)
    token = login_response.json()["access_token"]

    response = await client.post("/api/v1/auth/verify", json={"token": token})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["username"] == USERNAME
    assert body["sub"]
    assert body["expires_at"]


async def test_verify_invalid_token(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/verify", json={"token": "not.a.jwt"})
    assert response.status_code == 401


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
