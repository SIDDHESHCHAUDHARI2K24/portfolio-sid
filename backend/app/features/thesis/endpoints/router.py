"""Thesis routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import THESIS
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.thesis import service
from app.features.thesis.schemas import ThesisAdmin, ThesisCreate, ThesisPublic, ThesisUpdate

public_router = APIRouter(prefix="/api/v1/thesis", tags=["thesis"])
admin_router = APIRouter(
    prefix="/api/v1/admin/thesis",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[ThesisPublic])
async def list_public(session: DbSession) -> list[ThesisPublic]:
    items = await service.list_public_dicts(session)
    return [ThesisPublic(**d) for d in items]


@public_router.get("/{thesis_id}", response_model=ThesisPublic)
async def get_public(thesis_id: UUID, session: DbSession) -> ThesisPublic:
    entry_dict = await service.get_dict(session, thesis_id)
    if entry_dict is None:
        raise HTTPException(status_code=404, detail="Thesis entry not found")
    return ThesisPublic(**entry_dict)


@admin_router.get("", response_model=list[ThesisAdmin])
async def list_admin(session: DbSession) -> list[ThesisAdmin]:
    items = await service.list_admin_dicts(session)
    return [ThesisAdmin(**d) for d in items]


@admin_router.get("/{thesis_id}", response_model=ThesisAdmin)
async def get_admin(thesis_id: UUID, session: DbSession) -> ThesisAdmin:
    entry_dict = await service.get_dict(session, thesis_id)
    if entry_dict is None:
        raise HTTPException(status_code=404, detail="Thesis entry not found")
    return ThesisAdmin(**entry_dict)


@admin_router.post("", response_model=ThesisAdmin, status_code=201)
async def create(body: ThesisCreate, session: DbSession) -> ThesisAdmin:
    try:
        entry_dict = await service.create_dict(session, body)
        await revalidate([THESIS])
        return ThesisAdmin(**entry_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{thesis_id}", response_model=ThesisAdmin)
async def update(thesis_id: UUID, body: ThesisUpdate, session: DbSession) -> ThesisAdmin:
    try:
        entry_dict = await service.update_dict(session, thesis_id, body)
        await revalidate([THESIS])
        return ThesisAdmin(**entry_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{thesis_id}", status_code=204)
async def delete(thesis_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, thesis_id)
        await revalidate([THESIS])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
