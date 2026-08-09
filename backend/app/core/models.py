"""Declarative base, shared mixins, and core models.

Every feature slice imports from here; nothing in this file belongs to a
single feature. Conventions invariants 5-8 apply.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.core.enums import Audience, PublishStatus


class Base(DeclarativeBase):
    pass


# Native Postgres enum types, created once, shared by every column that
# stores audiences (TD-20 adds ARRAY(audience) per-item overrides).
# DEFAULT_AUDIENCE is deliberately absent: it is a Python-only sentinel
# for the uncategorised view and must never enter the database enum.
# values_callable: persist the lowercase enum VALUES, not member names.
AUDIENCE_ENUM = SAEnum(
    Audience, name="audience", native_enum=True, values_callable=lambda obj: [e.value for e in obj]
)
PUBLISH_STATUS_ENUM = SAEnum(
    PublishStatus,
    name="publish_status",
    native_enum=True,
    values_callable=lambda obj: [e.value for e in obj],
)


class UUIDMixin:
    """UUID primary key. Never a string column (index efficiency, rejects
    malformed values, no enumerable IDs on a public API)."""

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """UTC timestamps (stored timezone-aware, rendered viewer-local)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SortableMixin:
    """Manual ordering for lists (Books, Skills, Certifications...)."""

    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")


class PublishableMixin:
    """Draft/scheduled/published lifecycle shared by every content model.

    Subclasses that declare their own ``__table_args__`` must merge this
    mixin's index (declare a ``__table_args__`` that includes both).
    """

    status: Mapped[PublishStatus] = mapped_column(
        PUBLISH_STATUS_ENUM,
        nullable=False,
        default=PublishStatus.DRAFT,
        server_default=PublishStatus.DRAFT.value,
    )
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @declared_attr.directive
    def __table_args__(cls) -> tuple[Index, ...]:
        name = str(getattr(cls, "__tablename__", "publishable"))
        return (Index(f"ix_{name}_status_publish_at", "status", "publish_at"),)


class TopicTag(UUIDMixin, TimestampMixin, Base):
    """Topic tags (#ai, #fundraising) driving audience relevance.

    Shared across content types; each content type gets its own
    association table (never a polymorphic tag join).
    """

    __tablename__ = "topic_tags"
    __table_args__ = (
        CheckConstraint("slug = lower(slug)", name="ck_topic_tags_slug_lowercase"),
    )

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
