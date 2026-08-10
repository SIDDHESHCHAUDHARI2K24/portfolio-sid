"""Thesis service: returns dicts (not ORM) to avoid MissingGreenlet."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Audience, PublishStatus
from app.core.models import TopicTag
from app.features.thesis import repository
from app.features.thesis.models import Thesis
from app.features.thesis.schemas import ThesisCreate, ThesisUpdate


def _thesis_to_dict(thesis: Thesis) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": thesis.id,
        "title": thesis.title,
        "summary": thesis.summary,
        "drive_url": thesis.drive_url,
        "published_date": thesis.published_date,
        "sort_order": thesis.sort_order,
        "created_at": thesis.created_at,
        "updated_at": thesis.updated_at,
        "status": _s(thesis.status),
        "publish_at": thesis.publish_at,
        "published_at": thesis.published_at,
        "audience_override": (
            [_s(a) for a in thesis.audience_override] if thesis.audience_override else None
        ),
        "topic_tags": [
            {"id": t.id, "slug": t.slug, "label": t.label} for t in (thesis.topic_tags or [])
        ],
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    entries = await repository.list_public(session)
    return [_thesis_to_dict(e) for e in entries]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    entries = await repository.list_admin(session)
    return [_thesis_to_dict(e) for e in entries]


async def get_dict(session: AsyncSession, thesis_id: UUID) -> dict[str, object] | None:
    entry = await repository.get(session, thesis_id)
    if entry is None:
        return None
    return _thesis_to_dict(entry)


async def _resolve_tags(session: AsyncSession, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    tags = list((await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all())
    found = {t.slug for t in tags}
    missing = set(slugs) - found
    if missing:
        raise ValueError(f"unknown topic tag slugs: {', '.join(sorted(missing))}")
    return [t.id for t in tags]


async def create_dict(session: AsyncSession, data: ThesisCreate) -> dict[str, object]:
    tag_ids = await _resolve_tags(session, data.tag_slugs)
    entry_data = data.model_dump(exclude={"tag_slugs"})

    if entry_data.get("audience_override"):
        entry_data["audience_override"] = [Audience(a) for a in entry_data["audience_override"]]

    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)

    thesis = Thesis(**entry_data)
    thesis = await repository.create(session, thesis, tag_ids)
    await session.commit()
    return _thesis_to_dict(thesis)


async def update_dict(
    session: AsyncSession, thesis_id: UUID, data: ThesisUpdate
) -> dict[str, object]:
    entry = await repository.get(session, thesis_id)
    if entry is None:
        raise ValueError("thesis entry not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_slugs"})

    if update_data.get("audience_override"):
        update_data["audience_override"] = [Audience(a) for a in update_data["audience_override"]]

    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and entry.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)

    for key, value in update_data.items():
        setattr(entry, key, value)

    entry.updated_at = datetime.now(UTC)

    tag_ids = None
    if data.tag_slugs is not None:
        tag_ids = await _resolve_tags(session, data.tag_slugs)

    await repository.update(session, entry, tag_ids)
    await session.commit()
    return _thesis_to_dict(entry)


async def delete(session: AsyncSession, thesis_id: UUID) -> None:
    entry = await repository.get(session, thesis_id)
    if entry is None:
        raise ValueError("thesis entry not found")
    await repository.delete(session, entry)
    await session.commit()
