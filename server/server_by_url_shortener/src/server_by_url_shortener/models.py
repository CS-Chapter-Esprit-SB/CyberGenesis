"""Database models for the URL shortener service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class URLEntry(SQLModel, table=True):
    __tablename__ = "urls"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, min_length=1, max_length=32)
    original_url: str = Field(min_length=1, max_length=2048)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
