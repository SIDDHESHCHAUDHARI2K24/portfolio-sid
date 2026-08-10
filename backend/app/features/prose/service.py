"""ProsePage service: returns dicts (not ORM)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Audience, PublishStatus
from app.features.prose import repository
from app.features.prose.models import ProseGroup, ProsePage
from app.features.prose.schemas import ProsePageCreate, ProsePageUpdate


def _page_to_dict(page: ProsePage) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": page.id,
        "slug": page.slug,
        "title": page.title,
        "body": page.body,
        "group": _s(page.group),
        "cta_label": page.cta_label,
        "cta_url": page.cta_url,
        "sort_order": page.sort_order,
        "created_at": page.created_at,
        "updated_at": page.updated_at,
        "status": _s(page.status),
        "publish_at": page.publish_at,
        "published_at": page.published_at,
        "audience_override": (
            [_s(a) for a in page.audience_override] if page.audience_override else None
        ),
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    pages = await repository.list_public(session)
    return [_page_to_dict(p) for p in pages]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    pages = await repository.list_admin(session)
    return [_page_to_dict(p) for p in pages]


async def get_dict(session: AsyncSession, page_id: UUID) -> dict[str, object] | None:
    page = await repository.get(session, page_id)
    if page is None:
        return None
    return _page_to_dict(page)


async def get_by_slug_dict(session: AsyncSession, slug: str) -> dict[str, object] | None:
    page = await repository.get_by_slug(session, slug)
    if page is None:
        return None
    return _page_to_dict(page)


async def list_by_group_dicts(session: AsyncSession, group: str) -> list[dict[str, object]]:
    pages = await repository.list_by_group(session, group)
    return [_page_to_dict(p) for p in pages]


async def create_dict(session: AsyncSession, data: ProsePageCreate) -> dict[str, object]:
    entry_data = data.model_dump()
    raw_group = entry_data["group"]
    entry_data["group"] = ProseGroup(raw_group) if isinstance(raw_group, str) else raw_group
    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)
    if entry_data.get("audience_override"):
        entry_data["audience_override"] = [Audience(a) for a in entry_data["audience_override"]]
    page = ProsePage(**entry_data)
    page = await repository.create(session, page)
    await session.commit()
    return _page_to_dict(page)


async def update_dict(
    session: AsyncSession, page_id: UUID, data: ProsePageUpdate
) -> dict[str, object]:
    page = await repository.get(session, page_id)
    if page is None:
        raise ValueError("prose page not found")

    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("group") and isinstance(update_data["group"], str):
        update_data["group"] = ProseGroup(update_data["group"])
    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and page.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)
    if update_data.get("audience_override"):
        update_data["audience_override"] = [Audience(a) for a in update_data["audience_override"]]

    for key, value in update_data.items():
        setattr(page, key, value)

    page.updated_at = datetime.now(UTC)
    await repository.update(session, page)
    await session.commit()
    return _page_to_dict(page)


async def delete(session: AsyncSession, page_id: UUID) -> None:
    page = await repository.get(session, page_id)
    if page is None:
        raise ValueError("prose page not found")
    await repository.delete(session, page)
    await session.commit()
