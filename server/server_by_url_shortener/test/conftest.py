"""Shared fixtures for URL shortener tests using an in-process SQLite database."""

from __future__ import annotations

import pathlib
import sys
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from server_by_url_shortener.db import get_session  # noqa: E402
from server_by_url_shortener.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client(tmp_path: pathlib.Path) -> AsyncIterator[AsyncClient]:
    db_path = tmp_path / "test_url_shortener.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)
    await engine.dispose()
