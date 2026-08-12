"""Gateway middleware and dependency protecting routes with JWT.

``JWTAuthMiddleware`` is an ASGI middleware meant to be mounted at the API
gateway level. It blocks every request that lacks a valid ``Authorization:
Bearer <token>`` header (except public paths such as login/register), and
forwards the authenticated identity to downstream services as ``X-User-Id``
and ``X-Username`` request headers.
"""

from __future__ import annotations

from typing import Annotated

import jwt as pyjwt
from fastapi import Header, HTTPException, status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from server_by_auth.security import decode_token

DEFAULT_PUBLIC_PATHS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/verify",
]


class JWTAuthMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        public_paths: list[str] | None = None,
    ) -> None:
        self.app = app
        self._public_paths = list(public_paths or DEFAULT_PUBLIC_PATHS)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        if request.method == "OPTIONS" or request.url.path in self._public_paths:
            await self.app(scope, receive, send)
            return

        token = _extract_bearer_token(request)
        if token is None:
            await _unauthorized(scope, receive, send)
            return

        try:
            claims = decode_token(token)
        except pyjwt.PyJWTError:
            await _unauthorized(scope, receive, send)
            return

        enriched = _scope_with_identity(scope, claims)
        await self.app(enriched, receive, send)


def _extract_bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


async def _unauthorized(scope: Scope, receive: Receive, send: Send) -> None:
    response = JSONResponse({"detail": "authentication required"}, status_code=401)
    await response(scope, receive, send)


def _scope_with_identity(scope: Scope, claims: dict[str, object]) -> Scope:
    """Inject authenticated identity into the request scope for downstream services."""
    user_id = str(claims.get("sub", ""))
    username = str(claims.get("username", ""))
    headers = list(scope.get("headers", []))
    headers.append((b"x-user-id", user_id.encode()))
    headers.append((b"x-username", username.encode()))
    return {**scope, "headers": headers}


async def require_auth(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    """FastAPI dependency validating the Bearer token for route protection."""
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
        )
    token = authorization[7:].strip()
    try:
        return decode_token(token)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        ) from None
