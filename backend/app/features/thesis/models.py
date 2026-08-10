"""Thesis feature: investment thesis entries linking to Google Drive documents."""

from datetime import date

from sqlalchemy import Column, Date, ForeignKey, String, Table, Text
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

thesis_topic_tags = Table(
    "thesis_topic_tags",
    Base.metadata,
    Column(
        "thesis_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("thesis_entries.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_tag_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("topic_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Thesis(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    __tablename__ = "thesis_entries"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    drive_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    published_date: Mapped[date] = mapped_column(Date, nullable=False)
    audience_override: Mapped[list[Audience] | None] = mapped_column(
        postgresql.ARRAY(AUDIENCE_ENUM),
    )

    topic_tags: Mapped[list[TopicTag]] = relationship(secondary=thesis_topic_tags, lazy="selectin")
