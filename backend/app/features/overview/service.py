"""OverviewIntro service: orchestration. Returns dicts (not ORM objects)
to avoid MissingGreenlet from expired attributes after flush.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PublishStatus
from app.features.overview import repository
from app.features.overview.models import VALID_AUDIENCES, OverviewIntro
from app.features.overview.schemas import OverviewIntroCreate, OverviewIntroUpdate


def _intro_to_dict(intro: OverviewIntro) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": intro.id,
        "audience": intro.audience,
        "headline": intro.headline,
        "body": intro.body,
        "hero_image_key": intro.hero_image_key,
        "cta_label": intro.cta_label,
        "cta_url": intro.cta_url,
        "created_at": intro.created_at,
        "updated_at": intro.updated_at,
        "status": _s(intro.status),
        "publish_at": intro.publish_at,
        "published_at": intro.published_at,
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    intros = await repository.list_public(session)
    return [_intro_to_dict(i) for i in intros]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    intros = await repository.list_admin(session)
    return [_intro_to_dict(i) for i in intros]


async def get_by_audience_dict(session: AsyncSession, audience: str) -> dict[str, object] | None:
    intro = await repository.get_by_audience(session, audience)
    if intro is None:
        return None
    return _intro_to_dict(intro)


async def get_by_id_dict(session: AsyncSession, intro_id: UUID) -> dict[str, object] | None:
    intro = await repository.get_by_id(session, intro_id)
    if intro is None:
        return None
    return _intro_to_dict(intro)


async def create_dict(session: AsyncSession, data: OverviewIntroCreate) -> dict[str, object]:
    if data.audience not in VALID_AUDIENCES:
        raise ValueError(f"invalid audience: {data.audience}")

    existing = await repository.get_by_audience(session, data.audience)
    if existing is not None:
        raise ValueError(f"overview intro already exists for audience: {data.audience}")

    entry_data = data.model_dump()
    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)

    intro = OverviewIntro(**entry_data)
    await repository.create(session, intro)
    await session.commit()
    return _intro_to_dict(intro)


async def update_dict(
    session: AsyncSession, intro_id: UUID, data: OverviewIntroUpdate
) -> dict[str, object]:
    intro = await repository.get_by_id(session, intro_id)
    if intro is None:
        raise ValueError("overview intro not found")

    update_data = data.model_dump(exclude_unset=True)
    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and intro.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)

    for key, value in update_data.items():
        setattr(intro, key, value)

    intro.updated_at = datetime.now(UTC)
    await repository.update(session, intro)
    await session.commit()
    return _intro_to_dict(intro)


async def delete(session: AsyncSession, intro_id: UUID) -> None:
    intro = await repository.get_by_id(session, intro_id)
    if intro is None:
        raise ValueError("overview intro not found")
    await repository.delete(session, intro)
    await session.commit()
