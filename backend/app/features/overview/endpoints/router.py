"""Overview routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import OVERVIEW
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.overview import service
from app.features.overview.schemas import (
    OverviewIntroAdmin,
    OverviewIntroCreate,
    OverviewIntroPublic,
    OverviewIntroUpdate,
)

public_router = APIRouter(prefix="/api/v1/overview", tags=["overview"])
admin_router = APIRouter(
    prefix="/api/v1/admin/overview",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[OverviewIntroPublic])
async def list_public(session: DbSession) -> list[OverviewIntroPublic]:
    items = await service.list_public_dicts(session)
    return [OverviewIntroPublic(**d) for d in items]


@public_router.get("/{audience}", response_model=OverviewIntroPublic)
async def get_public(audience: str, session: DbSession) -> OverviewIntroPublic:
    intro_dict = await service.get_by_audience_dict(session, audience)
    if intro_dict is None:
        raise HTTPException(status_code=404, detail="Overview intro not found")
    return OverviewIntroPublic(**intro_dict)


@admin_router.get("", response_model=list[OverviewIntroAdmin])
async def list_admin(session: DbSession) -> list[OverviewIntroAdmin]:
    items = await service.list_admin_dicts(session)
    return [OverviewIntroAdmin(**d) for d in items]


@admin_router.get("/{intro_id}", response_model=OverviewIntroAdmin)
async def get_admin(intro_id: UUID, session: DbSession) -> OverviewIntroAdmin:
    intro_dict = await service.get_by_id_dict(session, intro_id)
    if intro_dict is None:
        raise HTTPException(status_code=404, detail="Overview intro not found")
    return OverviewIntroAdmin(**intro_dict)


@admin_router.post("", response_model=OverviewIntroAdmin, status_code=201)
async def create(body: OverviewIntroCreate, session: DbSession) -> OverviewIntroAdmin:
    try:
        intro_dict = await service.create_dict(session, body)
        await revalidate([OVERVIEW])
        return OverviewIntroAdmin(**intro_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{intro_id}", response_model=OverviewIntroAdmin)
async def update(
    intro_id: UUID, body: OverviewIntroUpdate, session: DbSession
) -> OverviewIntroAdmin:
    try:
        intro_dict = await service.update_dict(session, intro_id, body)
        await revalidate([OVERVIEW])
        return OverviewIntroAdmin(**intro_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{intro_id}", status_code=204)
async def delete(intro_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, intro_id)
        await revalidate([OVERVIEW])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
