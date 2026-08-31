"""Timeline routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import PROJECTS, TIMELINE
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.projects import service as projects_service
from app.features.projects.schemas import ProjectPublic
from app.features.timeline import service
from app.features.timeline.schemas import (
    TimelineEntryAdmin,
    TimelineEntryCreate,
    TimelineEntryPublic,
    TimelineEntryUpdate,
)

public_router = APIRouter(prefix="/api/v1/timeline", tags=["timeline"])
admin_router = APIRouter(
    prefix="/api/v1/admin/timeline",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[TimelineEntryPublic])
async def list_public(session: DbSession) -> list[TimelineEntryPublic]:
    items = await service.list_public_dicts(session)
    return [TimelineEntryPublic(**d) for d in items]


@public_router.get("/{entry_id}", response_model=TimelineEntryPublic)
async def get_public(entry_id: UUID, session: DbSession) -> TimelineEntryPublic:
    entry_dict = await service.get_public_dict(session, entry_id)
    if entry_dict is None:
        raise HTTPException(status_code=404, detail="Timeline entry not found")
    return TimelineEntryPublic(**entry_dict)


@public_router.get("/{entry_id}/projects", response_model=list[ProjectPublic])
async def list_public_projects(entry_id: UUID, session: DbSession) -> list[ProjectPublic]:
    entry_dict = await service.get_public_dict(session, entry_id)
    if entry_dict is None:
        raise HTTPException(status_code=404, detail="Timeline entry not found")
    projects = await projects_service.list_public_by_timeline_dict(session, entry_id)
    return [ProjectPublic(**d) for d in projects]


@admin_router.get("", response_model=list[TimelineEntryAdmin])
async def list_admin(session: DbSession) -> list[TimelineEntryAdmin]:
    items = await service.list_admin_dicts(session)
    return [TimelineEntryAdmin(**d) for d in items]


@admin_router.get("/{entry_id}", response_model=TimelineEntryAdmin)
async def get_admin(entry_id: UUID, session: DbSession) -> TimelineEntryAdmin:
    entry_dict = await service.get_dict(session, entry_id)
    if entry_dict is None:
        raise HTTPException(status_code=404, detail="Timeline entry not found")
    return TimelineEntryAdmin(**entry_dict)


@admin_router.post("", response_model=TimelineEntryAdmin, status_code=201)
async def create(body: TimelineEntryCreate, session: DbSession) -> TimelineEntryAdmin:
    try:
        entry_dict = await service.create_dict(session, body)
        await revalidate([TIMELINE, PROJECTS])
        return TimelineEntryAdmin(**entry_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{entry_id}", response_model=TimelineEntryAdmin)
async def update(
    entry_id: UUID, body: TimelineEntryUpdate, session: DbSession
) -> TimelineEntryAdmin:
    try:
        entry_dict = await service.update_dict(session, entry_id, body)
        await revalidate([TIMELINE, PROJECTS])
        return TimelineEntryAdmin(**entry_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{entry_id}", status_code=204)
async def delete(entry_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, entry_id)
        await revalidate([TIMELINE, PROJECTS])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
