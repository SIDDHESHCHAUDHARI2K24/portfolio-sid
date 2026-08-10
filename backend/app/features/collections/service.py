"""Collections service: returns dicts (not ORM), triggered cover lookup on create."""

from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PublishStatus
from app.core.storage import StorageAdapter
from app.features.collections import repository
from app.features.collections.covers import CoverResult, fetch_and_store_cover
from app.features.collections.models import (
    CollectionItem,
    CollectionKind,
    CollectionStatus,
    ExternalSource,
)
from app.features.collections.schemas import CollectionItemCreate, CollectionItemUpdate


def _item_to_dict(item: CollectionItem) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": item.id,
        "title": item.title,
        "creator": item.creator,
        "kind": _s(item.kind),
        "section": item.section,
        "cover_key": item.cover_key,
        "external_id": item.external_id,
        "external_source": _s(item.external_source) if item.external_source else None,
        "status": _s(item.status_) if item.status_ else None,
        "note": item.note,
        "sort_order": item.sort_order,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "status_": _s(item.status),
        "publish_at": item.publish_at,
        "published_at": item.published_at,
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    items = await repository.list_public(session)
    return [_item_to_dict(i) for i in items]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    items = await repository.list_admin(session)
    return [_item_to_dict(i) for i in items]


async def get_dict(session: AsyncSession, item_id: UUID) -> dict[str, object] | None:
    item = await repository.get(session, item_id)
    if item is None:
        return None
    return _item_to_dict(item)


async def create_dict(session: AsyncSession, data: CollectionItemCreate) -> dict[str, object]:
    entry_data = data.model_dump(exclude={"publish_status"})
    raw_kind = entry_data["kind"]
    entry_data["kind"] = CollectionKind(raw_kind) if isinstance(raw_kind, str) else raw_kind
    if isinstance(entry_data.get("external_source"), str):
        val = entry_data["external_source"]
        entry_data["external_source"] = ExternalSource(val) if val else None
    if isinstance(entry_data.get("status"), str):
        val = entry_data["status"]
        entry_data["status_"] = CollectionStatus(val) if val else None
    else:
        entry_data["status_"] = entry_data.pop("status", None)

    pub_status = PublishStatus(data.publish_status)
    entry_data["status"] = pub_status
    if pub_status == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)

    item = CollectionItem(**entry_data)
    item = await repository.create(session, item)
    await session.commit()
    return _item_to_dict(item)


async def update_dict(
    session: AsyncSession, item_id: UUID, data: CollectionItemUpdate
) -> dict[str, object]:
    item = await repository.get(session, item_id)
    if item is None:
        raise ValueError("collection item not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"publish_status"})
    if "kind" in update_data and isinstance(update_data["kind"], str):
        update_data["kind"] = CollectionKind(update_data["kind"])
    if "external_source" in update_data and isinstance(update_data["external_source"], str):
        val = update_data["external_source"]
        update_data["external_source"] = ExternalSource(val) if val else None
    if "status" in update_data and isinstance(update_data["status"], str):
        val = update_data["status"]
        update_data["status_"] = CollectionStatus(val) if val else None
        del update_data["status"]

    if data.publish_status is not None:
        update_data["status"] = PublishStatus(data.publish_status)
        if (
            update_data["status"] == PublishStatus.PUBLISHED
            and item.status != PublishStatus.PUBLISHED
        ):
            update_data["published_at"] = datetime.now(UTC)

    for key, value in update_data.items():
        setattr(item, key, value)

    item.updated_at = datetime.now(UTC)
    await repository.update(session, item)
    await session.commit()
    return _item_to_dict(item)


async def delete(session: AsyncSession, item_id: UUID) -> None:
    item = await repository.get(session, item_id)
    if item is None:
        raise ValueError("collection item not found")
    await repository.delete(session, item)
    await session.commit()


async def lookup_cover(
    title: str,
    kind: str,
    adapter: StorageAdapter,
    client: httpx.AsyncClient,
) -> CoverResult:
    return await fetch_and_store_cover(title, kind, adapter, client)
