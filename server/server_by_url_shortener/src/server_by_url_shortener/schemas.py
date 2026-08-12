"""Pydantic request/response schemas for the URL shortener API."""

from __future__ import annotations

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel

from server_by_url_shortener.models import URLEntry


class URLInput(BaseModel):
    url: AnyHttpUrl


class URLOutput(BaseModel):
    id: int
    code: str
    url: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entry(cls, entry: URLEntry) -> URLOutput:
        return cls(
            id=entry.id,
            code=entry.code,
            url=entry.original_url,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
