"""Resume routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import RESUMES
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.resumes import service
from app.features.resumes.schemas import (
    ResumeAdmin,
    ResumeCreate,
    ResumePublic,
    ResumeUpdate,
)

public_router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])
admin_router = APIRouter(
    prefix="/api/v1/admin/resumes",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[ResumePublic])
async def list_public(session: DbSession) -> list[ResumePublic]:
    items = await service.list_public_dicts(session)
    return [ResumePublic(**d) for d in items]


@admin_router.get("", response_model=list[ResumeAdmin])
async def list_admin(session: DbSession) -> list[ResumeAdmin]:
    items = await service.list_admin_dicts(session)
    return [ResumeAdmin(**d) for d in items]


@admin_router.get("/{resume_id}", response_model=ResumeAdmin)
async def get_admin(resume_id: UUID, session: DbSession) -> ResumeAdmin:
    item = await service.get_dict(session, resume_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeAdmin(**item)


@admin_router.post("", response_model=ResumeAdmin, status_code=201)
async def create(body: ResumeCreate, session: DbSession) -> ResumeAdmin:
    try:
        item = await service.create_dict(session, body)
        await revalidate([RESUMES])
        return ResumeAdmin(**item)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{resume_id}", response_model=ResumeAdmin)
async def update(resume_id: UUID, body: ResumeUpdate, session: DbSession) -> ResumeAdmin:
    try:
        item = await service.update_dict(session, resume_id, body)
        await revalidate([RESUMES])
        return ResumeAdmin(**item)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{resume_id}", status_code=204)
async def delete(resume_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, resume_id)
        await revalidate([RESUMES])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
