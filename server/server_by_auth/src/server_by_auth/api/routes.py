"""Auth REST endpoints: register, login and token verification."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from server_by_auth import crud, security
from server_by_auth.config import settings
from server_by_auth.db import get_session
from server_by_auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    VerifyRequest,
    VerifyResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, session: SessionDep) -> UserOut:
    user = await crud.create_user(session, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already exists"
        )
    return UserOut(id=user.id, username=user.username, created_at=user.created_at)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    user = await crud.authenticate(session, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )
    token = security.create_access_token(user.id, user.username)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify(payload: VerifyRequest) -> VerifyResponse:
    try:
        claims = security.decode_token(payload.token)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        ) from None
    expires_at = datetime.fromtimestamp(int(claims["exp"]), UTC)
    return VerifyResponse(
        valid=True,
        sub=str(claims["sub"]),
        username=str(claims.get("username")),
        expires_at=expires_at,
    )
