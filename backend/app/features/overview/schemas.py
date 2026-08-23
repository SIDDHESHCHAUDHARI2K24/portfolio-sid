"""OverviewIntro Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OverviewIntroPublic(BaseModel):
    id: UUID
    audience: str
    headline: str
    body: str
    hero_image_key: str | None
    cta_label: str | None
    cta_url: str | None
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime


class OverviewIntroAdmin(OverviewIntroPublic):
    status: str
    publish_at: datetime | None
    published_at: datetime | None


class OverviewIntroCreate(BaseModel):
    audience: str
    headline: str = ""
    body: str = ""
    hero_image_key: str | None = None
    cta_label: str | None = None
    cta_url: str | None = None
    status: str = "draft"
    publish_at: datetime | None = None
    is_pinned: bool = False


class OverviewIntroUpdate(BaseModel):
    headline: str | None = None
    body: str | None = None
    hero_image_key: str | None = None
    cta_label: str | None = None
    cta_url: str | None = None
    status: str | None = None
    publish_at: datetime | None = None
    is_pinned: bool | None = None
