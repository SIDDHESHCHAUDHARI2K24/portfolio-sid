"""Skills service: returns dicts (not ORM) to avoid MissingGreenlet.

Skills have no publishing, no tags, no audience override — just CRUD.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.features.skills import repository
from app.features.skills.models import Skill, SkillSection
from app.features.skills.schemas import SkillCreate, SkillUpdate


def _skill_to_dict(skill: Skill) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": skill.id,
        "name": skill.name,
        "section": _s(skill.section),
        "subsection": skill.subsection,
        "icon_slug": skill.icon_slug,
        "icon_key": skill.icon_key,
        "icon_url": get_storage().get_url(skill.icon_key) if skill.icon_key else None,
        "sort_order": skill.sort_order,
        "created_at": skill.created_at,
        "updated_at": skill.updated_at,
    }


async def list_dicts(session: AsyncSession) -> list[dict[str, object]]:
    skills = await repository.list_all(session)
    return [_skill_to_dict(s) for s in skills]


async def get_dict(session: AsyncSession, skill_id: UUID) -> dict[str, object] | None:
    skill = await repository.get(session, skill_id)
    if skill is None:
        return None
    return _skill_to_dict(skill)


async def create_dict(session: AsyncSession, data: SkillCreate) -> dict[str, object]:
    entry_data = data.model_dump()
    raw_section = entry_data["section"]
    entry_data["section"] = (
        SkillSection(raw_section) if isinstance(raw_section, str) else raw_section
    )
    skill = Skill(**entry_data)
    skill = await repository.create(session, skill)
    await session.commit()
    return _skill_to_dict(skill)


async def update_dict(
    session: AsyncSession, skill_id: UUID, data: SkillUpdate
) -> dict[str, object]:
    skill = await repository.get(session, skill_id)
    if skill is None:
        raise ValueError("skill not found")

    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("section") and isinstance(update_data["section"], str):
        update_data["section"] = SkillSection(update_data["section"])

    for key, value in update_data.items():
        setattr(skill, key, value)

    skill.updated_at = datetime.now(UTC)

    await repository.update(session, skill)
    await session.commit()
    return _skill_to_dict(skill)


async def delete(session: AsyncSession, skill_id: UUID) -> None:
    skill = await repository.get(session, skill_id)
    if skill is None:
        raise ValueError("skill not found")
    await repository.delete(session, skill)
    await session.commit()
