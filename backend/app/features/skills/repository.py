"""Skills repository: queries only, never imports FastAPI.

Skills are always visible — no public_filter, no publishing logic.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.skills.models import Skill


async def list_all(session: AsyncSession) -> list[Skill]:
    stmt = select(Skill).order_by(
        Skill.section.asc(), Skill.subsection.asc(), Skill.sort_order.asc()
    )
    return list((await session.scalars(stmt)).all())


async def get(session: AsyncSession, skill_id: UUID) -> Skill | None:
    return await session.get(Skill, skill_id)


async def create(session: AsyncSession, skill: Skill) -> Skill:
    session.add(skill)
    await session.flush()
    return skill


async def update(session: AsyncSession, skill: Skill) -> Skill:
    await session.flush()
    return skill


async def delete(session: AsyncSession, skill: Skill) -> None:
    await session.delete(skill)
    await session.flush()
