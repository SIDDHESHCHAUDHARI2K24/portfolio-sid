"""ProsePage repository: queries only, never imports FastAPI."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries import public_filter
from app.features.prose.models import ProsePage


async def list_public(session: AsyncSession) -> list[ProsePage]:
    stmt = (
        select(ProsePage)
        .where(public_filter(ProsePage))
        .order_by(ProsePage.group.asc(), ProsePage.sort_order.asc())
    )
    return list((await session.scalars(stmt)).all())


async def list_admin(session: AsyncSession) -> list[ProsePage]:
    stmt = select(ProsePage).order_by(ProsePage.group.asc(), ProsePage.sort_order.asc())
    return list((await session.scalars(stmt)).all())


async def get(session: AsyncSession, page_id: UUID) -> ProsePage | None:
    return await session.get(ProsePage, page_id)


async def get_by_slug(session: AsyncSession, slug: str) -> ProsePage | None:
    stmt = select(ProsePage).where(ProsePage.slug == slug).where(public_filter(ProsePage))
    return (await session.scalars(stmt)).first()


async def list_by_group(session: AsyncSession, group: str) -> list[ProsePage]:
    stmt = (
        select(ProsePage)
        .where(public_filter(ProsePage))
        .where(ProsePage.group == group)
        .order_by(ProsePage.sort_order.asc())
    )
    return list((await session.scalars(stmt)).all())


async def create(session: AsyncSession, page: ProsePage) -> ProsePage:
    session.add(page)
    await session.flush()
    return page


async def update(session: AsyncSession, page: ProsePage) -> ProsePage:
    await session.flush()
    return page


async def delete(session: AsyncSession, page: ProsePage) -> None:
    await session.delete(page)
    await session.flush()
