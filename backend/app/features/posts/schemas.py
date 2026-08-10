"""Posts Pydantic schemas.

No ``from_attributes=True`` — ORM-to-dict conversion happens in the router
via ``_to_dict`` to avoid MissingGreenlet.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class TagRef(BaseModel):
    id: UUID
    slug: str
    label: str


class PostPublic(BaseModel):
    id: UUID
    title: str
    summary: str | None
    url: str
    platform: str
    published_date: date | None
    collections: list[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime
    topic_tags: list[TagRef] = []
    audience_override: list[str] | None = None


class PostAdmin(PostPublic):
    status: str
    publish_at: datetime | None
    published_at: datetime | None


class PostCreate(BaseModel):
    title: str
    summary: str | None = None
    url: str
    platform: str
    published_date: date | None = None
    collections: list[str] = []
    tag_slugs: list[str] = []
    audience_override: list[str] | None = None
    sort_order: int = 0
    status: str = "draft"
    publish_at: datetime | None = None


class PostUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    url: str | None = None
    platform: str | None = None
    published_date: date | None = None
    collections: list[str] | None = None
    tag_slugs: list[str] | None = None
    audience_override: list[str] | None = None
    sort_order: int | None = None
    status: str | None = None
    publish_at: datetime | None = None
