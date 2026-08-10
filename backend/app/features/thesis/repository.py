"""Thesis repository: queries only, never imports FastAPI.

``list_public`` applies ``public_filter``; admin bypasses it.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import TopicTag
from app.core.queries import public_filter
from app.features.thesis.models import Thesis


async def list_public(session: AsyncSession) -> list[Thesis]:
    stmt = (
        select(Thesis)
        .where(public_filter(Thesis))
        .options(selectinload(Thesis.topic_tags))
        .order_by(Thesis.published_date.desc(), Thesis.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def list_admin(session: AsyncSession) -> list[Thesis]:
    stmt = (
        select(Thesis)
        .options(selectinload(Thesis.topic_tags))
        .order_by(Thesis.published_date.desc(), Thesis.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def get(session: AsyncSession, thesis_id: UUID) -> Thesis | None:
    return await session.get(Thesis, thesis_id, options=[selectinload(Thesis.topic_tags)])


async def create(
    session: AsyncSession,
    thesis: Thesis,
    tag_ids: list[UUID] | None = None,
) -> Thesis:
    tags: list[TopicTag] = []
    if tag_ids:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
    thesis.topic_tags = tags
    session.add(thesis)
    await session.flush()
    return thesis


async def update(
    session: AsyncSession,
    thesis: Thesis,
    tag_ids: list[UUID] | None = None,
) -> Thesis:
    if tag_ids is not None:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
        thesis.topic_tags = tags
    else:
        _ = thesis.topic_tags
    await session.flush()
    return thesis


async def delete(session: AsyncSession, thesis: Thesis) -> None:
    await session.delete(thesis)
    await session.flush()
