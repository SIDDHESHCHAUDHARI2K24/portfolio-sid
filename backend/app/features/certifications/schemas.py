"""Certifications Pydantic schemas.

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


class CertificationPublic(BaseModel):
    id: UUID
    title: str
    issuer: str
    kind: str
    issued_date: date
    expires_date: date | None
    credential_url: str | None
    file_key: str | None
    file_type: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    topic_tags: list[TagRef] = []


class CertificationAdmin(CertificationPublic):
    status: str
    publish_at: datetime | None
    published_at: datetime | None
    audience_override: list[str] | None


class CertificationCreate(BaseModel):
    title: str
    issuer: str
    kind: str
    issued_date: date
    expires_date: date | None = None
    credential_url: str | None = None
    file_key: str | None = None
    file_type: str | None = None
    tag_slugs: list[str] = []
    audience_override: list[str] | None = None
    sort_order: int = 0
    status: str = "draft"
    publish_at: datetime | None = None


class CertificationUpdate(BaseModel):
    title: str | None = None
    issuer: str | None = None
    kind: str | None = None
    issued_date: date | None = None
    expires_date: date | None = None
    credential_url: str | None = None
    file_key: str | None = None
    file_type: str | None = None
    tag_slugs: list[str] | None = None
    audience_override: list[str] | None = None
    sort_order: int | None = None
    status: str | None = None
    publish_at: datetime | None = None
