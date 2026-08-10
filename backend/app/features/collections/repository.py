"""Collections repository: queries only, never imports FastAPI."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries import public_filter
from app.features.collections.models import CollectionItem


async def list_public(session: AsyncSession) -> list[CollectionItem]:
    stmt = (
        select(CollectionItem)
        .where(public_filter(CollectionItem))
        .order_by(
            CollectionItem.kind.asc(),
            CollectionItem.section.asc(),
            CollectionItem.sort_order.asc(),
        )
    )
    return list((await session.scalars(stmt)).all())


async def list_admin(session: AsyncSession) -> list[CollectionItem]:
    stmt = select(CollectionItem).order_by(
        CollectionItem.kind.asc(), CollectionItem.section.asc(), CollectionItem.sort_order.asc()
    )
    return list((await session.scalars(stmt)).all())


async def get(session: AsyncSession, item_id: UUID) -> CollectionItem | None:
    return await session.get(CollectionItem, item_id)


async def create(session: AsyncSession, item: CollectionItem) -> CollectionItem:
    session.add(item)
    await session.flush()
    return item


async def update(session: AsyncSession, item: CollectionItem) -> CollectionItem:
    await session.flush()
    return item


async def delete(session: AsyncSession, item: CollectionItem) -> None:
    await session.delete(item)
    await session.flush()
