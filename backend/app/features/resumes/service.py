"""Resume service: orchestration, validation. Returns dicts."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.resumes import repository
from app.features.resumes.models import Resume, ResumeVariant
from app.features.resumes.schemas import ResumeCreate, ResumeUpdate


def _to_dict(resume: Resume) -> dict[str, object]:
    return {
        "id": resume.id,
        "variant": resume.variant.value,
        "label": resume.label,
        "file_key": resume.file_key,
        "is_active": resume.is_active,
        "created_at": resume.created_at,
        "updated_at": resume.updated_at,
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    resumes = await repository.list_active(session)
    return [_to_dict(r) for r in resumes]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    resumes = await repository.list_all(session)
    return [_to_dict(r) for r in resumes]


async def get_dict(session: AsyncSession, resume_id: UUID) -> dict[str, object] | None:
    resume = await repository.get(session, resume_id)
    if resume is None:
        return None
    return _to_dict(resume)


async def create_dict(session: AsyncSession, data: ResumeCreate) -> dict[str, object]:
    entry_data = data.model_dump()
    entry_data["variant"] = ResumeVariant(entry_data["variant"])
    resume = Resume(**entry_data)
    resume = await repository.create(session, resume)
    await session.commit()
    return _to_dict(resume)


async def update_dict(
    session: AsyncSession, resume_id: UUID, data: ResumeUpdate
) -> dict[str, object]:
    resume = await repository.get(session, resume_id)
    if resume is None:
        raise ValueError("resume not found")

    update_data = data.model_dump(exclude_unset=True)
    if "variant" in update_data and isinstance(update_data["variant"], str):
        update_data["variant"] = ResumeVariant(update_data["variant"])

    for key, value in update_data.items():
        setattr(resume, key, value)

    resume.updated_at = datetime.now(UTC)
    await repository.update(session, resume)
    await session.commit()
    return _to_dict(resume)


async def delete(session: AsyncSession, resume_id: UUID) -> None:
    resume = await repository.get(session, resume_id)
    if resume is None:
        raise ValueError("resume not found")
    await repository.delete(session, resume)
    await session.commit()
