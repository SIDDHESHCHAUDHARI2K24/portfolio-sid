"""Resume service: orchestration, validation. Returns dicts."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.features.resumes import repository
from app.features.resumes.models import ALLOWED_VARIANTS, Resume
from app.features.resumes.schemas import ResumeCreate, ResumeUpdate


def _to_dict(resume: Resume) -> dict[str, object]:
    # ``variant`` is now plain String; legacy rows may still hold an enum
    # instance during rollout, so unwrap ``.value`` defensively.
    variant: object = resume.variant
    if hasattr(variant, "value"):
        # enum instance — getattr avoids mypy attr-defined error on object
        variant = getattr(variant, "value")  # noqa: B009
    return {
        "id": resume.id,
        "variant": variant,
        "label": resume.label,
        "file_key": resume.file_key,
        "file_url": get_storage().get_url(resume.file_key) if resume.file_key else None,
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
    variant = entry_data.get("variant")
    # Pydantic already validates, but service is the defence-in-depth gate
    # for callers that bypass schemas (e.g. seed scripts).
    if not isinstance(variant, str) or variant not in ALLOWED_VARIANTS:
        allowed = ", ".join(sorted(ALLOWED_VARIANTS))
        raise ValueError(f"variant must be one of: {allowed} (got {variant!r})")
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
    if (
        "variant" in update_data
        and isinstance(update_data["variant"], str)
        and update_data["variant"] not in ALLOWED_VARIANTS
    ):
        allowed = ", ".join(sorted(ALLOWED_VARIANTS))
        raise ValueError(f"variant must be one of: {allowed} (got {update_data['variant']!r})")

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
