"""Projects service: orchestration, validation. Returns dicts (not ORM objects)
to avoid MissingGreenlet from expired attributes after flush.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Audience, PublishStatus
from app.core.models import TopicTag
from app.features.projects import repository
from app.features.projects.models import Project, ProjectAttachment


def _attachment_to_dict(att: ProjectAttachment) -> dict[str, object]:
    from app.core.storage import get_storage

    kind = att.kind.value if hasattr(att.kind, "value") else str(att.kind)
    return {
        "id": att.id,
        "kind": kind,
        "label": att.label,
        "sort_order": att.sort_order,
        "storage_key": att.storage_key,
        "url": get_storage().get_url(att.storage_key),
        "project_id": att.project_id,
    }


def _project_to_dict(project: Project) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": project.id,
        "title": project.title,
        "slug": project.slug,
        "summary": project.summary,
        "description": project.description,
        "video_url": project.video_url,
        "timeline_entry_id": project.timeline_entry_id,
        "sort_order": project.sort_order,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "status": _s(project.status),
        "publish_at": project.publish_at,
        "published_at": project.published_at,
        "audience_override": (
            [_s(a) for a in project.audience_override] if project.audience_override else None
        ),
        "topic_tags": [
            {"id": t.id, "slug": t.slug, "label": t.label} for t in (project.topic_tags or [])
        ],
        "attachments": [_attachment_to_dict(a) for a in (project.attachments or [])],
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    projects = await repository.list_public(session)
    return [_project_to_dict(p) for p in projects]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    projects = await repository.list_admin(session)
    return [_project_to_dict(p) for p in projects]


async def get_dict(session: AsyncSession, project_id: UUID) -> dict[str, object] | None:
    project = await repository.get(session, project_id)
    if project is None:
        return None
    return _project_to_dict(project)


async def get_by_slug_dict(session: AsyncSession, slug: str) -> dict[str, object] | None:
    project = await repository.get_by_slug(session, slug)
    if project is None:
        return None
    return _project_to_dict(project)


async def _resolve_tags(session: AsyncSession, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    tags = list((await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all())
    found = {t.slug for t in tags}
    missing = set(slugs) - found
    if missing:
        raise ValueError(f"unknown topic tag slugs: {', '.join(sorted(missing))}")
    return [t.id for t in tags]


async def create_dict(session: AsyncSession, data: object) -> dict[str, object]:
    from app.features.projects.schemas import ProjectCreate

    assert isinstance(data, ProjectCreate)
    tag_ids = await _resolve_tags(session, data.tag_slugs)
    entry_data = data.model_dump(exclude={"tag_slugs"})
    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)
    if entry_data.get("audience_override"):
        entry_data["audience_override"] = [Audience(a) for a in entry_data["audience_override"]]
    project = Project(**entry_data)
    project = await repository.create(session, project, tag_ids)
    await session.commit()
    return _project_to_dict(project)


async def update_dict(session: AsyncSession, project_id: UUID, data: object) -> dict[str, object]:
    from app.features.projects.schemas import ProjectUpdate

    assert isinstance(data, ProjectUpdate)
    project = await repository.get(session, project_id)
    if project is None:
        raise ValueError("project not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_slugs"})
    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and project.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)
    if update_data.get("audience_override"):
        update_data["audience_override"] = [Audience(a) for a in update_data["audience_override"]]

    for key, value in update_data.items():
        setattr(project, key, value)

    project.updated_at = datetime.now(UTC)

    tag_ids = None
    if data.tag_slugs is not None:
        tag_ids = await _resolve_tags(session, data.tag_slugs)

    await repository.update(session, project, tag_ids)
    await session.commit()
    return _project_to_dict(project)


async def delete(session: AsyncSession, project_id: UUID) -> None:
    project = await repository.get(session, project_id)
    if project is None:
        raise ValueError("project not found")
    await repository.delete(session, project)
    await session.commit()
