"""Skills routers: public read-only, admin full CRUD. No publishing logic."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import SKILLS
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.skills import service
from app.features.skills.schemas import SkillAdmin, SkillCreate, SkillPublic, SkillUpdate

public_router = APIRouter(prefix="/api/v1/skills", tags=["skills"])
admin_router = APIRouter(
    prefix="/api/v1/admin/skills",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[SkillPublic])
async def list_public(session: DbSession) -> list[SkillPublic]:
    items = await service.list_dicts(session)
    return [SkillPublic(**d) for d in items]


@admin_router.get("", response_model=list[SkillAdmin])
async def list_admin(session: DbSession) -> list[SkillAdmin]:
    items = await service.list_dicts(session)
    return [SkillAdmin(**d) for d in items]


@admin_router.get("/{skill_id}", response_model=SkillAdmin)
async def get_admin(skill_id: UUID, session: DbSession) -> SkillAdmin:
    skill_dict = await service.get_dict(session, skill_id)
    if skill_dict is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillAdmin(**skill_dict)


@admin_router.post("", response_model=SkillAdmin, status_code=201)
async def create(body: SkillCreate, session: DbSession) -> SkillAdmin:
    try:
        skill_dict = await service.create_dict(session, body)
        await revalidate([SKILLS])
        return SkillAdmin(**skill_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{skill_id}", response_model=SkillAdmin)
async def update(skill_id: UUID, body: SkillUpdate, session: DbSession) -> SkillAdmin:
    try:
        skill_dict = await service.update_dict(session, skill_id, body)
        await revalidate([SKILLS])
        return SkillAdmin(**skill_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{skill_id}", status_code=204)
async def delete(skill_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, skill_id)
        await revalidate([SKILLS])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
