"""Contact repository: queries only, never imports FastAPI."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.contact.models import ContactItem, ContactProfile


async def get_profile(session: AsyncSession) -> ContactProfile | None:
    stmt = select(ContactProfile).limit(1)
    return (await session.scalars(stmt)).first()


async def update_profile(session: AsyncSession, profile: ContactProfile) -> ContactProfile:
    await session.flush()
    return profile


async def list_items(session: AsyncSession) -> list[ContactItem]:
    stmt = select(ContactItem).order_by(ContactItem.sort_order, ContactItem.created_at)
    return list((await session.scalars(stmt)).all())


async def delete_all_items(session: AsyncSession) -> None:
    await session.execute(delete(ContactItem))
    await session.flush()
