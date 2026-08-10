"""Form submission repository: queries only, never imports FastAPI."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.forms.models import FormSubmission, FormType


async def list_all_admin(
    session: AsyncSession,
    form_type: FormType | None = None,
    is_read: bool | None = None,
) -> list[FormSubmission]:
    stmt = select(FormSubmission).order_by(FormSubmission.created_at.desc())
    if form_type is not None:
        stmt = stmt.where(FormSubmission.form_type == form_type)
    if is_read is not None:
        stmt = stmt.where(FormSubmission.is_read.is_(is_read))
    return list((await session.scalars(stmt)).all())


async def get(session: AsyncSession, submission_id: UUID) -> FormSubmission | None:
    return await session.get(FormSubmission, submission_id)


async def create(session: AsyncSession, submission: FormSubmission) -> FormSubmission:
    session.add(submission)
    await session.flush()
    return submission


async def update(session: AsyncSession, submission: FormSubmission) -> FormSubmission:
    await session.flush()
    return submission
