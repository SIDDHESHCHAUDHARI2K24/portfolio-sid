"""Projects Pydantic schemas.

Public and admin shapes. No ``from_attributes=True`` — ORM-to-dict
conversion happens in the service layer via ``_to_dict`` to avoid
MissingGreenlet when async session attributes expire after flush.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.features.projects.models import ProjectAttachmentKind


class TagRef(BaseModel):
    id: UUID
    slug: str
    label: str


class AttachmentRef(BaseModel):
    id: UUID
    kind: str
    label: str
    sort_order: int
    url: str


class ProjectPublic(BaseModel):
    id: UUID
    title: str
    slug: str
    summary: str | None
    description: str | None
    video_url: str | None
    timeline_entry_id: UUID | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    topic_tags: list[TagRef] = []
    attachments: list[AttachmentRef] = []


class ProjectAdmin(ProjectPublic):
    status: str
    publish_at: datetime | None
    published_at: datetime | None
    audience_override: list[str] | None


class ProjectCreate(BaseModel):
    title: str
    slug: str
    summary: str | None = None
    description: str | None = None
    timeline_entry_id: UUID | None = None
    video_url: str | None = None
    tag_slugs: list[str] = []
    audience_override: list[str] | None = None
    status: str = "draft"
    publish_at: datetime | None = None
    is_pinned: bool = False


class ProjectUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    summary: str | None = None
    description: str | None = None
    timeline_entry_id: UUID | None = None
    video_url: str | None = None
    tag_slugs: list[str] | None = None
    audience_override: list[str] | None = None
    status: str | None = None
    publish_at: datetime | None = None
    is_pinned: bool | None = None


class AttachmentCreate(BaseModel):
    kind: ProjectAttachmentKind
    label: str
    sort_order: int = 0


class AttachmentAdmin(AttachmentCreate):
    id: UUID
    project_id: UUID
    storage_key: str
    url: str
