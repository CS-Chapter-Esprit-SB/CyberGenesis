"""CRUD REST endpoints for short URLs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from server_by_url_shortener import crud
from server_by_url_shortener.db import get_session
from server_by_url_shortener.schemas import URLInput, URLOutput

router = APIRouter(prefix="/urls", tags=["urls"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=URLOutput, status_code=status.HTTP_201_CREATED)
async def create_url(payload: URLInput, session: SessionDep) -> URLOutput:
    entry = await crud.create_url_entry(session, str(payload.url))
    return URLOutput.from_entry(entry)


@router.get("/{code}", response_model=URLOutput)
async def get_url(code: str, session: SessionDep) -> URLOutput:
    entry = await crud.get_url_entry(session, code)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )
    return URLOutput.from_entry(entry)


@router.put("/{code}", response_model=URLOutput)
async def update_url(code: str, payload: URLInput, session: SessionDep) -> URLOutput:
    entry = await crud.update_url_entry(session, code, str(payload.url))
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )
    return URLOutput.from_entry(entry)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(code: str, session: SessionDep) -> Response:
    deleted = await crud.delete_url_entry(session, code)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="URL not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
