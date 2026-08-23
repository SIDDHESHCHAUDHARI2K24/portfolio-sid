"""Collections Pydantic schemas — no topic tags, no audience override."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.features.collections.models import CollectionKind, CollectionStatus, ExternalSource


class CollectionItemPublic(BaseModel):
    id: UUID
    title: str
    creator: str | None
    kind: str
    section: str | None
    cover_key: str | None
    external_id: str | None
    external_source: str | None
    status: str | None
    note: str | None
    sort_order: int
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime


class CollectionItemAdmin(CollectionItemPublic):
    status_: str  # publish status (draft/scheduled/published)
    publish_at: datetime | None
    published_at: datetime | None


class CollectionItemCreate(BaseModel):
    title: str
    creator: str | None = None
    kind: CollectionKind
    section: str | None = None
    cover_key: str | None = None
    external_id: str | None = None
    external_source: ExternalSource | None = None
    status: CollectionStatus | None = None
    note: str | None = None
    sort_order: int = 0
    publish_status: str = "draft"
    publish_at: datetime | None = None
    is_pinned: bool = False


class CollectionItemUpdate(BaseModel):
    title: str | None = None
    creator: str | None = None
    kind: CollectionKind | None = None
    section: str | None = None
    cover_key: str | None = None
    external_id: str | None = None
    external_source: ExternalSource | None = None
    status: CollectionStatus | None = None
    note: str | None = None
    sort_order: int | None = None
    publish_status: str | None = None
    publish_at: datetime | None = None
    is_pinned: bool | None = None


class CoverLookupRequest(BaseModel):
    title: str
    kind: CollectionKind


class CoverLookupResponse(BaseModel):
    status: str
    cover_key: str | None = None
