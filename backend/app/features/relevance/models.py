"""Relevance models: the admin-editable audience → topic tag map."""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Audience
from app.core.models import AUDIENCE_ENUM, Base, TimestampMixin, TopicTag, UUIDMixin


class AudienceTagMap(UUIDMixin, TimestampMixin, Base):
    """Which topic tags make content relevant to which audience.

    Lives in the database, not a config file: changing the mapping must
    not require a deploy. Topic tags only (conventions invariant 9) —
    collection tags never enter this table.
    """

    __tablename__ = "audience_tag_map"
    __table_args__ = (
        UniqueConstraint("audience", "topic_tag_id", name="uq_audience_tag_map_audience_tag"),
    )

    audience: Mapped[Audience] = mapped_column(AUDIENCE_ENUM, nullable=False)
    topic_tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topic_tags.id", ondelete="CASCADE"), nullable=False
    )

    topic_tag: Mapped[TopicTag] = relationship()
