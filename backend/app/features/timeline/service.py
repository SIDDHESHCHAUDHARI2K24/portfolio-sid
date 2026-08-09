"""Timeline service: orchestration, validation. Returns dicts (not ORM objects)
to avoid MissingGreenlet from expired attributes after flush.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Audience, PublishStatus
from app.core.models import TopicTag
from app.features.timeline import repository
from app.features.timeline.models import TimelineEntry, TimelineKind
from app.features.timeline.schemas import TimelineEntryCreate, TimelineEntryUpdate


def _entry_to_dict(entry: TimelineEntry) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": entry.id,
        "kind": _s(entry.kind),
        "title": entry.title,
        "organisation": entry.organisation,
        "location": entry.location,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "summary": entry.summary,
        "highlights": entry.highlights,
        "external_url": entry.external_url,
        "sort_order": entry.sort_order,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "status": _s(entry.status),
        "publish_at": entry.publish_at,
        "published_at": entry.published_at,
        "audience_override": (
            [_s(a) for a in entry.audience_override] if entry.audience_override else None
        ),
        "topic_tags": [
            {"id": t.id, "slug": t.slug, "label": t.label} for t in (entry.topic_tags or [])
        ],
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    entries = await repository.list_public(session)
    return [_entry_to_dict(e) for e in entries]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    entries = await repository.list_admin(session)
    return [_entry_to_dict(e) for e in entries]


async def get_dict(session: AsyncSession, entry_id: UUID) -> dict[str, object] | None:
    entry = await repository.get(session, entry_id)
    if entry is None:
        return None
    return _entry_to_dict(entry)


async def _resolve_tags(session: AsyncSession, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    tags = list((await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all())
    found = {t.slug for t in tags}
    missing = set(slugs) - found
    if missing:
        raise ValueError(f"unknown topic tag slugs: {', '.join(sorted(missing))}")
    return [t.id for t in tags]


async def create_dict(session: AsyncSession, data: TimelineEntryCreate) -> dict[str, object]:
    tag_ids = await _resolve_tags(session, data.tag_slugs)
    entry_data = data.model_dump(exclude={"tag_slugs"})
    raw_kind = entry_data["kind"]
    entry_data["kind"] = TimelineKind(raw_kind) if isinstance(raw_kind, str) else raw_kind
    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)
    if entry_data.get("audience_override"):
        entry_data["audience_override"] = [Audience(a) for a in entry_data["audience_override"]]
    entry = TimelineEntry(**entry_data)
    entry = await repository.create(session, entry, tag_ids)
    await session.commit()
    return _entry_to_dict(entry)


async def update_dict(
    session: AsyncSession, entry_id: UUID, data: TimelineEntryUpdate
) -> dict[str, object]:
    entry = await repository.get(session, entry_id)
    if entry is None:
        raise ValueError("timeline entry not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_slugs"})
    if update_data.get("kind") and isinstance(update_data["kind"], str):
        update_data["kind"] = TimelineKind(update_data["kind"])
    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and entry.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)
    if update_data.get("audience_override"):
        update_data["audience_override"] = [Audience(a) for a in update_data["audience_override"]]

    for key, value in update_data.items():
        setattr(entry, key, value)

    # Ensure updated_at is set locally to avoid MissingGreenlet after flush.
    entry.updated_at = datetime.now(UTC)

    tag_ids = None
    if data.tag_slugs is not None:
        tag_ids = await _resolve_tags(session, data.tag_slugs)

    await repository.update(session, entry, tag_ids)
    await session.commit()
    return _entry_to_dict(entry)


async def delete(session: AsyncSession, entry_id: UUID) -> None:
    entry = await repository.get(session, entry_id)
    if entry is None:
        raise ValueError("timeline entry not found")
    await repository.delete(session, entry)
    await session.commit()
