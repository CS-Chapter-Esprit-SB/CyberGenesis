"""Shared fixtures for rate limiter tests using an in-memory fake Redis."""

from __future__ import annotations

import pathlib
import sys

import pytest_asyncio
from fakeredis import FakeAsyncRedis

SRC_DIR = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest_asyncio.fixture
async def fake_redis() -> FakeAsyncRedis:
    client = FakeAsyncRedis(decode_responses=True)
    yield client
    await client.aclose()
