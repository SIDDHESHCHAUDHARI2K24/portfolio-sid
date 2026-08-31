"""Projects routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import PROJECTS, TIMELINE
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.projects import service
from app.features.projects.schemas import (
    ProjectAdmin,
    ProjectCreate,
    ProjectPublic,
    ProjectUpdate,
)

public_router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
admin_router = APIRouter(
    prefix="/api/v1/admin/projects",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[ProjectPublic])
async def list_public(session: DbSession) -> list[ProjectPublic]:
    items = await service.list_public_dicts(session)
    return [ProjectPublic(**d) for d in items]


@public_router.get("/{slug}", response_model=ProjectPublic)
async def get_public(slug: str, session: DbSession) -> ProjectPublic:
    project_dict = await service.get_by_slug_dict(session, slug)
    if project_dict is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectPublic(**project_dict)


@admin_router.get("", response_model=list[ProjectAdmin])
async def list_admin(session: DbSession) -> list[ProjectAdmin]:
    items = await service.list_admin_dicts(session)
    return [ProjectAdmin(**d) for d in items]


@admin_router.get("/{project_id}", response_model=ProjectAdmin)
async def get_admin(project_id: UUID, session: DbSession) -> ProjectAdmin:
    project_dict = await service.get_dict(session, project_id)
    if project_dict is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectAdmin(**project_dict)


@admin_router.post("", response_model=ProjectAdmin, status_code=201)
async def create(body: ProjectCreate, session: DbSession) -> ProjectAdmin:
    try:
        project_dict = await service.create_dict(session, body)
        await revalidate([PROJECTS, TIMELINE])
        return ProjectAdmin(**project_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{project_id}", response_model=ProjectAdmin)
async def update(project_id: UUID, body: ProjectUpdate, session: DbSession) -> ProjectAdmin:
    try:
        project_dict = await service.update_dict(session, project_id, body)
        await revalidate([PROJECTS, TIMELINE])
        return ProjectAdmin(**project_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{project_id}", status_code=204)
async def delete(project_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, project_id)
        await revalidate([PROJECTS, TIMELINE])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
