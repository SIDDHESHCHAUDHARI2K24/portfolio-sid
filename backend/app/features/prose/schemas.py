"""ProsePage Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.features.prose.models import ProseGroup


class ProsePagePublic(BaseModel):
    id: UUID
    slug: str
    title: str
    body: str
    group: str
    cta_label: str | None
    cta_url: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ProsePageAdmin(ProsePagePublic):
    status: str
    publish_at: datetime | None
    published_at: datetime | None
    audience_override: list[str] | None


class ProsePageCreate(BaseModel):
    slug: str
    title: str
    body: str = ""
    group: ProseGroup
    cta_label: str | None = None
    cta_url: str | None = None
    sort_order: int = 0
    audience_override: list[str] | None = None
    status: str = "draft"
    publish_at: datetime | None = None


class ProsePageUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    body: str | None = None
    group: ProseGroup | None = None
    cta_label: str | None = None
    cta_url: str | None = None
    sort_order: int | None = None
    audience_override: list[str] | None = None
    status: str | None = None
    publish_at: datetime | None = None
