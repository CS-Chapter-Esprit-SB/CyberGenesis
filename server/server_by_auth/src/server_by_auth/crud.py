"""User persistence and authentication helpers."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from server_by_auth.models import User
from server_by_auth.security import hash_password, verify_password


async def create_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Create a user with a bcrypt-hashed password, or None on conflict."""
    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return None
    await session.refresh(user)
    return user


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.exec(select(User).where(User.username == username))
    return result.one_or_none()


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Return the user when credentials are valid, otherwise None."""
    user = await get_user_by_username(session, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
