"""ProsePage routers: public by-slug + list, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import PROSE
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.prose import service
from app.features.prose.schemas import (
    ProsePageAdmin,
    ProsePageCreate,
    ProsePagePublic,
    ProsePageUpdate,
)

public_router = APIRouter(prefix="/api/v1/prose", tags=["prose"])
admin_router = APIRouter(
    prefix="/api/v1/admin/prose",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[ProsePagePublic])
async def list_public(session: DbSession) -> list[ProsePagePublic]:
    pages = await service.list_public_dicts(session)
    return [ProsePagePublic(**d) for d in pages]


@public_router.get("/slug/{slug}", response_model=ProsePagePublic)
async def get_by_slug(slug: str, session: DbSession) -> ProsePagePublic:
    page_dict = await service.get_by_slug_dict(session, slug)
    if page_dict is None:
        raise HTTPException(status_code=404, detail="Prose page not found")
    return ProsePagePublic(**page_dict)


@admin_router.get("", response_model=list[ProsePageAdmin])
async def list_admin(session: DbSession) -> list[ProsePageAdmin]:
    pages = await service.list_admin_dicts(session)
    return [ProsePageAdmin(**d) for d in pages]


@admin_router.get("/{page_id}", response_model=ProsePageAdmin)
async def get_admin(page_id: UUID, session: DbSession) -> ProsePageAdmin:
    page_dict = await service.get_dict(session, page_id)
    if page_dict is None:
        raise HTTPException(status_code=404, detail="Prose page not found")
    return ProsePageAdmin(**page_dict)


@admin_router.post("", response_model=ProsePageAdmin, status_code=201)
async def create(body: ProsePageCreate, session: DbSession) -> ProsePageAdmin:
    try:
        page_dict = await service.create_dict(session, body)
        await revalidate([PROSE])
        return ProsePageAdmin(**page_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{page_id}", response_model=ProsePageAdmin)
async def update(page_id: UUID, body: ProsePageUpdate, session: DbSession) -> ProsePageAdmin:
    try:
        page_dict = await service.update_dict(session, page_id, body)
        await revalidate([PROSE])
        return ProsePageAdmin(**page_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{page_id}", status_code=204)
async def delete(page_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, page_id)
        await revalidate([PROSE])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
