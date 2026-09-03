"""ContactProfile routers: public read-only, admin get/update singleton."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import CONTACT
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.contact import service
from app.features.contact.schemas import ContactAdmin, ContactPublic, ContactUpdate

public_router = APIRouter(prefix="/api/v1/contact", tags=["contact"])
admin_router = APIRouter(
    prefix="/api/v1/admin/contact",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=ContactPublic)
async def get_public(session: DbSession) -> ContactPublic:
    profile = await service.get_dict(session)
    if profile is None:
        raise HTTPException(status_code=404, detail="Contact profile not found")
    return ContactPublic(**profile)


@admin_router.get("", response_model=ContactAdmin)
async def get_admin(session: DbSession) -> ContactAdmin:
    profile = await service.get_dict(session)
    if profile is None:
        raise HTTPException(status_code=404, detail="Contact profile not found")
    return ContactAdmin(**profile)


@admin_router.put("", response_model=ContactAdmin)
async def update(body: ContactUpdate, session: DbSession) -> ContactAdmin:
    try:
        profile = await service.update_dict(session, body)
        await revalidate([CONTACT])
        return ContactAdmin(**profile)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
