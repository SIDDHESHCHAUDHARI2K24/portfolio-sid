"""Relevance routes: public cached map, admin matrix read/replace, tag CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import admin_auth
from app.features.relevance import service
from app.features.relevance.schemas import (
    AdminMapUpdate,
    RelevanceMapResponse,
    TagCreate,
    TagOut,
    TagUpdate,
)

public_router = APIRouter(prefix="/api/v1/relevance", tags=["relevance"])
admin_router = APIRouter(
    prefix="/api/v1/admin/relevance", tags=["admin"], dependencies=admin_auth()
)
tag_admin_router = APIRouter(prefix="/api/v1/admin/tags", tags=["admin"], dependencies=admin_auth())

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("/map", response_model=RelevanceMapResponse)
async def get_map(response: Response, session: DbSession) -> dict[str, list[str]]:
    """Small, rarely changing: cache aggressively (conventions invariant 3
    ships this in every content page payload)."""
    response.headers["Cache-Control"] = "public, max-age=300"
    return await service.get_map_payload(session)


@admin_router.get("/map", response_model=RelevanceMapResponse)
async def admin_get_map(session: DbSession) -> dict[str, list[str]]:
    """Full current matrix: every audience present, empty ones included."""
    return await service.get_map_payload(session)


@admin_router.put("/map", response_model=RelevanceMapResponse)
async def admin_update_map(body: AdminMapUpdate, session: DbSession) -> dict[str, list[str]]:
    try:
        return await service.update_map(session, body.mapping)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@tag_admin_router.get("", response_model=list[TagOut])
async def list_tags(session: DbSession) -> list[TagOut]:
    return await service.list_tags(session)


@tag_admin_router.post("", response_model=TagOut, status_code=201)
async def create_tag(body: TagCreate, session: DbSession) -> TagOut:
    try:
        return await service.create_tag(session, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@tag_admin_router.patch("/{tag_id}", response_model=TagOut)
async def rename_tag(tag_id: UUID, body: TagUpdate, session: DbSession) -> TagOut:
    try:
        return await service.rename_tag(session, tag_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@tag_admin_router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: UUID, session: DbSession) -> None:
    try:
        await service.delete_tag(session, tag_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
