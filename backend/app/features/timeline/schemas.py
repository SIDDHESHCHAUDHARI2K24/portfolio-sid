"""Timeline Pydantic schemas.

Public and admin shapes. No ``from_attributes=True`` — ORM-to-dict
conversion happens in the router via ``_entity_to_dict`` to avoid
MissingGreenlet when async session attributes expire after flush.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.features.timeline.models import TimelineKind


class TagRef(BaseModel):
    id: UUID
    slug: str
    label: str


class TimelineEntryPublic(BaseModel):
    id: UUID
    kind: str
    title: str
    organisation: str
    location: str | None
    start_date: date
    end_date: date | None
    summary: str | None
    highlights: list[str] | None
    external_url: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    topic_tags: list[TagRef] = []


class TimelineEntryAdmin(TimelineEntryPublic):
    status: str
    publish_at: datetime | None
    published_at: datetime | None
    audience_override: list[str] | None


class TimelineEntryCreate(BaseModel):
    kind: TimelineKind
    title: str
    organisation: str
    location: str | None = None
    start_date: date
    end_date: date | None = None
    summary: str | None = None
    highlights: list[str] | None = None
    external_url: str | None = None
    tag_slugs: list[str] = []
    audience_override: list[str] | None = None
    status: str = "draft"
    publish_at: datetime | None = None
    is_pinned: bool = False

    @model_validator(mode="after")
    def end_not_before_start(self) -> "TimelineEntryCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class TimelineEntryUpdate(BaseModel):
    kind: TimelineKind | None = None
    title: str | None = None
    organisation: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    summary: str | None = None
    highlights: list[str] | None = None
    external_url: str | None = None
    tag_slugs: list[str] | None = None
    audience_override: list[str] | None = None
    status: str | None = None
    publish_at: datetime | None = None
    is_pinned: bool | None = None

    @model_validator(mode="after")
    def end_not_before_start(self) -> "TimelineEntryUpdate":
        if (
            self.end_date is not None
            and self.start_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self
