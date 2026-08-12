"""Unit tests for password hashing and JWT handling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from server_by_auth import security
from server_by_auth.config import settings


def test_hash_and_verify_password() -> None:
    hashed = security.hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert security.verify_password("s3cret-password", hashed)
    assert not security.verify_password("wrong-password", hashed)


def test_hash_is_salted() -> None:
    first = security.hash_password("same-password")
    second = security.hash_password("same-password")
    assert first != second


def test_create_and_decode_token() -> None:
    token = security.create_access_token(42, "alice")
    claims = security.decode_token(token)
    assert claims["sub"] == "42"
    assert claims["username"] == "alice"
    assert claims["iss"] == settings.jwt_issuer
    assert claims["iat"]
    assert claims["exp"]


def test_expired_token_raises() -> None:
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "username": "bob",
        "iss": settings.jwt_issuer,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    token = pyjwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        security.decode_token(token)


def test_tampered_token_raises() -> None:
    token = security.create_access_token(42, "alice")
    with pytest.raises(pyjwt.InvalidSignatureError):
        security.decode_token(token + "tampered")


def test_wrong_issuer_raises() -> None:
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "username": "bob",
        "iss": "someone-else",
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }
    token = pyjwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(pyjwt.InvalidIssuerError):
        security.decode_token(token)
