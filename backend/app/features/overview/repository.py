"""OverviewIntro repository: queries only, never imports FastAPI."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queries import public_filter
from app.features.overview.models import OverviewIntro


async def list_public(session: AsyncSession) -> list[OverviewIntro]:
    stmt = (
        select(OverviewIntro).where(public_filter(OverviewIntro)).order_by(OverviewIntro.audience)
    )
    return list((await session.scalars(stmt)).all())


async def list_admin(session: AsyncSession) -> list[OverviewIntro]:
    stmt = select(OverviewIntro).order_by(OverviewIntro.audience)
    return list((await session.scalars(stmt)).all())


async def get_by_audience(session: AsyncSession, audience: str) -> OverviewIntro | None:
    stmt = select(OverviewIntro).where(OverviewIntro.audience == audience)
    return (await session.scalars(stmt)).first()


async def get_by_id(session: AsyncSession, intro_id: UUID) -> OverviewIntro | None:
    return await session.get(OverviewIntro, intro_id)


async def create(session: AsyncSession, intro: OverviewIntro) -> OverviewIntro:
    session.add(intro)
    await session.flush()
    return intro


async def update(session: AsyncSession, intro: OverviewIntro) -> OverviewIntro:
    await session.flush()
    return intro


async def delete(session: AsyncSession, intro: OverviewIntro) -> None:
    await session.delete(intro)
    await session.flush()
