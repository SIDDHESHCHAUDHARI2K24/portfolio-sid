"""ContactProfile repository: queries only, never imports FastAPI."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.contact.models import ContactProfile


async def get(session: AsyncSession) -> ContactProfile | None:
    stmt = select(ContactProfile).limit(1)
    return (await session.scalars(stmt)).first()


async def update(session: AsyncSession, profile: ContactProfile) -> ContactProfile:
    await session.flush()
    return profile
