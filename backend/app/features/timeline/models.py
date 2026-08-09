"""Timeline feature: unified education/experience model.

One model, not two — education and experience differ only in labels and
render identically in one chronological list. Separate models would mean
union queries and duplicated tag/publishing logic.
"""

import enum

from sqlalchemy import Column, Date, ForeignKey, Index, String, Table, Text, text
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


class TimelineKind(enum.StrEnum):
    EDUCATION = "education"
    EXPERIENCE = "experience"


timeline_topic_tags = Table(
    "timeline_topic_tags",
    Base.metadata,
    Column(
        "timeline_entry_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("timeline_entries.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_tag_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("topic_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class TimelineEntry(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    """A single chronological entry covering education and professional history."""

    __tablename__ = "timeline_entries"
    __table_args__ = (
        Index("ix_timeline_start_date", text("start_date DESC")),
    ) + PublishableMixin.__table_args__

    kind: Mapped[TimelineKind] = mapped_column(
        postgresql.ENUM(TimelineKind, name="timeline_kind", create_type=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    organisation: Mapped[str] = mapped_column(String(300), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300))
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text)
    highlights: Mapped[list[str] | None] = mapped_column(postgresql.JSONB)
    external_url: Mapped[str | None] = mapped_column(String(2000))
    audience_override: Mapped[list[Audience] | None] = mapped_column(
        postgresql.ARRAY(AUDIENCE_ENUM),
    )

    topic_tags: Mapped[list[TopicTag]] = relationship(
        secondary=timeline_topic_tags, lazy="selectin"
    )
