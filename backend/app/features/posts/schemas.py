"""Posts Pydantic schemas.

No ``from_attributes=True`` — ORM-to-dict conversion happens in the router
via ``_to_dict`` to avoid MissingGreenlet.
"""

import re
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SLUG_MAX = 200
BODY_MAX_BYTES = 100 * 1024


def _normalize_slug(value: str | None) -> str | None:
    if value is None:
        return None
    slug = value.strip().lower()
    if not slug:
        return None
    if len(slug) > SLUG_MAX or not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must be lowercase letters, digits and single hyphens (max 200)")
    return slug


def _check_body(value: str | None) -> str | None:
    if value is not None and len(value.encode("utf-8")) > BODY_MAX_BYTES:
        raise ValueError("body must be at most 100 KB")
    return value


class TagRef(BaseModel):
    id: UUID
    slug: str
    label: str


class PostPublic(BaseModel):
    id: UUID
    title: str
    summary: str | None
    url: str | None
    slug: str | None = None
    platform: str
    published_date: date | None
    collections: list[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    topic_tags: list[TagRef] = []
    audience_override: list[str] | None = None


class PostDetail(PostPublic):
    """Public detail of an internal post: the only public shape carrying ``body``."""

    body: str


class PostAdmin(PostPublic):
    body: str | None = None
    status: str
    publish_at: datetime | None
    published_at: datetime | None


class PostCreate(BaseModel):
    title: str
    summary: str | None = None
    url: str | None = None
    slug: str | None = None
    body: str | None = None
    platform: str
    published_date: date | None = None
    collections: list[str] = []
    tag_slugs: list[str] = []
    audience_override: list[str] | None = None
    sort_order: int = 0
    status: str = "draft"
    publish_at: datetime | None = None
    is_pinned: bool = False

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str | None) -> str | None:
        return _normalize_slug(v)

    @field_validator("body")
    @classmethod
    def _body(cls, v: str | None) -> str | None:
        return _check_body(v)


class PostUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    url: str | None = None
    slug: str | None = None
    body: str | None = None
    platform: str | None = None
    published_date: date | None = None
    collections: list[str] | None = None
    tag_slugs: list[str] | None = None
    audience_override: list[str] | None = None
    sort_order: int | None = None
    status: str | None = None
    publish_at: datetime | None = None
    is_pinned: bool | None = None

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str | None) -> str | None:
        return _normalize_slug(v)

    @field_validator("body")
    @classmethod
    def _body(cls, v: str | None) -> str | None:
        return _check_body(v)
