"""Posts routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import POSTS
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.posts import service
from app.features.posts.models import PostCollection
from app.features.posts.schemas import PostAdmin, PostCreate, PostPublic, PostUpdate

public_router = APIRouter(prefix="/api/v1/posts", tags=["posts"])
admin_router = APIRouter(
    prefix="/api/v1/admin/posts",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[PostPublic])
async def list_public(
    session: DbSession,
    collection: str | None = Query(None),
) -> list[PostPublic]:
    if collection:
        try:
            col = PostCollection(collection)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail=f"Unknown collection: {collection}"
            ) from exc
        items = await service.list_by_collection_dict(session, col)
    else:
        items = await service.list_public_dicts(session)
    return [PostPublic(**d) for d in items]


@public_router.get("/{post_id}", response_model=PostPublic)
async def get_public(post_id: UUID, session: DbSession) -> PostPublic:
    post_dict = await service.get_dict(session, post_id)
    if post_dict is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostPublic(**post_dict)


@admin_router.get("", response_model=list[PostAdmin])
async def list_admin(session: DbSession) -> list[PostAdmin]:
    items = await service.list_admin_dicts(session)
    return [PostAdmin(**d) for d in items]


@admin_router.get("/{post_id}", response_model=PostAdmin)
async def get_admin(post_id: UUID, session: DbSession) -> PostAdmin:
    post_dict = await service.get_dict(session, post_id)
    if post_dict is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostAdmin(**post_dict)


@admin_router.post("", response_model=PostAdmin, status_code=201)
async def create(body: PostCreate, session: DbSession) -> PostAdmin:
    try:
        post_dict = await service.create_dict(session, body)
        await revalidate([POSTS])
        return PostAdmin(**post_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{post_id}", response_model=PostAdmin)
async def update(post_id: UUID, body: PostUpdate, session: DbSession) -> PostAdmin:
    try:
        post_dict = await service.update_dict(session, post_id, body)
        await revalidate([POSTS])
        return PostAdmin(**post_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{post_id}", status_code=204)
async def delete(post_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, post_id)
        await revalidate([POSTS])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
