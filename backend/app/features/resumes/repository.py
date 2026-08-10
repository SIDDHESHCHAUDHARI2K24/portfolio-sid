"""Resume repository: queries only, never imports FastAPI."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.resumes.models import Resume


async def list_active(session: AsyncSession) -> list[Resume]:
    stmt = select(Resume).where(Resume.is_active.is_(True)).order_by(Resume.variant.asc())
    return list((await session.scalars(stmt)).all())


async def list_all(session: AsyncSession) -> list[Resume]:
    stmt = select(Resume).order_by(Resume.variant.asc())
    return list((await session.scalars(stmt)).all())


async def get(session: AsyncSession, resume_id: UUID) -> Resume | None:
    return await session.get(Resume, resume_id)


async def create(session: AsyncSession, resume: Resume) -> Resume:
    session.add(resume)
    await session.flush()
    return resume


async def update(session: AsyncSession, resume: Resume) -> Resume:
    await session.flush()
    return resume


async def delete(session: AsyncSession, resume: Resume) -> None:
    await session.delete(resume)
    await session.flush()
