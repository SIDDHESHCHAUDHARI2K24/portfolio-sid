"""Projects feature: portfolio projects with optional timeline cross-link and file attachments."""

import enum
import uuid

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Audience
from app.core.models import (
    AUDIENCE_ENUM,
    Base,
    PublishableMixin,
    SortableMixin,
    TimestampMixin,
    TopicTag,
    UUIDMixin,
)


class ProjectAttachmentKind(enum.StrEnum):
    PDF = "pdf"
    PPT = "ppt"
    IMAGE = "image"


project_topic_tags = Table(
    "project_topic_tags",
    Base.metadata,
    Column(
        "project_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_tag_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("topic_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Project(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    timeline_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("timeline_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    video_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    audience_override: Mapped[list[Audience] | None] = mapped_column(
        postgresql.ARRAY(AUDIENCE_ENUM),
    )

    topic_tags: Mapped[list[TopicTag]] = relationship(secondary=project_topic_tags, lazy="selectin")
    attachments: Mapped[list["ProjectAttachment"]] = relationship(
        "ProjectAttachment", lazy="selectin", cascade="all, delete-orphan"
    )
    timeline_entry: Mapped[object | None] = relationship(
        "TimelineEntry",
        primaryjoin="Project.timeline_entry_id == foreign(TimelineEntry.id)",
        viewonly=True,
        lazy="selectin",
    )


class ProjectAttachment(UUIDMixin, Base):
    __tablename__ = "project_attachments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[ProjectAttachmentKind] = mapped_column(
        postgresql.ENUM(ProjectAttachmentKind, name="project_attachment_kind", create_type=True),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
