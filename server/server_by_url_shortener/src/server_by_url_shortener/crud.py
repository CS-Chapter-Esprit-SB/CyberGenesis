"""CRUD operations for URL entries with collision-safe short-code allocation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from server_by_url_shortener.models import URLEntry
from server_by_url_shortener.shortcode import generate_short_code

MAX_CODE_ATTEMPTS = 5


class ShortCodeExhaustedError(RuntimeError):
    """Raised when a unique short code could not be allocated after retries."""


async def create_url_entry(session: AsyncSession, url: str) -> URLEntry:
    """Create a URL entry, retrying with a fresh code on collision."""
    for _ in range(MAX_CODE_ATTEMPTS):
        entry = URLEntry(code=generate_short_code(), original_url=url)
        session.add(entry)
        try:
            await session.commit()
            await session.refresh(entry)
            return entry
        except IntegrityError:
            await session.rollback()
    raise ShortCodeExhaustedError("could not allocate a unique short code")


async def get_url_entry(session: AsyncSession, code: str) -> URLEntry | None:
    result = await session.exec(select(URLEntry).where(URLEntry.code == code))
    return result.one_or_none()


async def update_url_entry(
    session: AsyncSession, code: str, url: str
) -> URLEntry | None:
    entry = await get_url_entry(session, code)
    if entry is None:
        return None
    entry.original_url = url
    entry.updated_at = datetime.now(UTC)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def delete_url_entry(session: AsyncSession, code: str) -> bool:
    entry = await get_url_entry(session, code)
    if entry is None:
        return False
    await session.delete(entry)
    await session.commit()
    return True
