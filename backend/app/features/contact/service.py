"""ContactProfile service: dicts in, dicts out (never ORM across the router)."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.contact import repository
from app.features.contact.models import ContactProfile
from app.features.contact.schemas import ContactUpdate


def _profile_to_dict(profile: ContactProfile) -> dict[str, str]:
    return {
        "email": profile.email,
        "linkedin_url": profile.linkedin_url,
        "linkedin_label": profile.linkedin_label,
        "cal_url": profile.cal_url,
        "cal_label": profile.cal_label,
        "github_url": profile.github_url,
        "consent_text": profile.consent_text,
    }


async def get_dict(session: AsyncSession) -> dict[str, str] | None:
    profile = await repository.get(session)
    if profile is None:
        return None
    return _profile_to_dict(profile)


async def update_dict(session: AsyncSession, data: ContactUpdate) -> dict[str, str]:
    profile = await repository.get(session)
    if profile is None:
        raise ValueError("contact profile not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(profile, key, value)

    profile.updated_at = datetime.now(UTC)
    await repository.update(session, profile)
    await session.commit()
    return _profile_to_dict(profile)
