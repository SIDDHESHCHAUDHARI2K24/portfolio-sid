"""Collections routers: public read-only + cover lookup, admin full CRUD."""

from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import COLLECTIONS
from app.core.database import get_session
from app.core.deps import admin_auth, get_storage_adapter
from app.core.revalidation import revalidate
from app.core.storage import StorageAdapter
from app.features.collections import service
from app.features.collections.schemas import (
    CollectionItemAdmin,
    CollectionItemCreate,
    CollectionItemPublic,
    CollectionItemUpdate,
    CoverLookupRequest,
    CoverLookupResponse,
)

public_router = APIRouter(prefix="/api/v1/collections", tags=["collections"])
admin_router = APIRouter(
    prefix="/api/v1/admin/collections",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[CollectionItemPublic])
async def list_public(session: DbSession) -> list[CollectionItemPublic]:
    items = await service.list_public_dicts(session)
    return [CollectionItemPublic(**d) for d in items]


@admin_router.get("", response_model=list[CollectionItemAdmin])
async def list_admin(session: DbSession) -> list[CollectionItemAdmin]:
    items = await service.list_admin_dicts(session)
    return [CollectionItemAdmin(**d) for d in items]


@admin_router.get("/{item_id}", response_model=CollectionItemAdmin)
async def get_admin(item_id: UUID, session: DbSession) -> CollectionItemAdmin:
    item_dict = await service.get_dict(session, item_id)
    if item_dict is None:
        raise HTTPException(status_code=404, detail="Collection item not found")
    return CollectionItemAdmin(**item_dict)


@admin_router.post("", response_model=CollectionItemAdmin, status_code=201)
async def create(body: CollectionItemCreate, session: DbSession) -> CollectionItemAdmin:
    try:
        item_dict = await service.create_dict(session, body)
        await revalidate([COLLECTIONS])
        return CollectionItemAdmin(**item_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{item_id}", response_model=CollectionItemAdmin)
async def update(
    item_id: UUID, body: CollectionItemUpdate, session: DbSession
) -> CollectionItemAdmin:
    try:
        item_dict = await service.update_dict(session, item_id, body)
        await revalidate([COLLECTIONS])
        return CollectionItemAdmin(**item_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{item_id}", status_code=204)
async def delete(item_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, item_id)
        await revalidate([COLLECTIONS])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@admin_router.post("/cover-lookup", response_model=CoverLookupResponse)
async def cover_lookup(
    body: CoverLookupRequest,
    adapter: Annotated[StorageAdapter, Depends(get_storage_adapter)],
) -> CoverLookupResponse:
    async with httpx.AsyncClient(timeout=20) as client:
        result = await service.lookup_cover(body.title, body.kind.value, adapter, client)
    return CoverLookupResponse(status=result.status, cover_key=result.cover_key)
