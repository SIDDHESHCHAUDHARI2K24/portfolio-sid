"""Timeline repository: queries only, never imports FastAPI.

``list_public`` must issue a constant number of queries regardless of
entry count (``selectinload`` tags, no N+1).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import TopicTag
from app.core.queries import public_filter
from app.features.timeline.models import TimelineEntry


async def list_public(session: AsyncSession) -> list[TimelineEntry]:
    stmt = (
        select(TimelineEntry)
        .where(public_filter(TimelineEntry))
        .options(selectinload(TimelineEntry.topic_tags))
        .order_by(TimelineEntry.start_date.desc(), TimelineEntry.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def list_admin(session: AsyncSession) -> list[TimelineEntry]:
    stmt = (
        select(TimelineEntry)
        .options(selectinload(TimelineEntry.topic_tags))
        .order_by(TimelineEntry.start_date.desc(), TimelineEntry.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def get(session: AsyncSession, entry_id: UUID) -> TimelineEntry | None:
    return await session.get(
        TimelineEntry, entry_id, options=[selectinload(TimelineEntry.topic_tags)]
    )


async def create(
    session: AsyncSession,
    entry: TimelineEntry,
    tag_ids: list[UUID] | None = None,
) -> TimelineEntry:
    tags: list[TopicTag] = []
    if tag_ids:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
    entry.topic_tags = tags
    session.add(entry)
    await session.flush()
    return entry


async def update(
    session: AsyncSession,
    entry: TimelineEntry,
    tag_ids: list[UUID] | None = None,
) -> TimelineEntry:
    if tag_ids is not None:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
        entry.topic_tags = tags
    else:
        # Keep existing tags unchanged; ensure relationship is loaded
        _ = entry.topic_tags
    await session.flush()
    return entry


async def delete(session: AsyncSession, entry: TimelineEntry) -> None:
    await session.delete(entry)
    await session.flush()
