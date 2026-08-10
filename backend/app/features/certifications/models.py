"""Certifications feature: technical/business certifications with file uploads."""

import enum
from datetime import date

from sqlalchemy import Column, Date, ForeignKey, String, Table
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


class CertKind(enum.StrEnum):
    TECHNICAL = "technical"
    BUSINESS = "business"


class CertFileType(enum.StrEnum):
    PDF = "pdf"
    IMAGE = "image"


certification_topic_tags = Table(
    "certification_topic_tags",
    Base.metadata,
    Column(
        "certification_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("certifications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_tag_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("topic_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Certification(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    __tablename__ = "certifications"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[CertKind] = mapped_column(
        postgresql.ENUM(CertKind, name="cert_kind", create_type=True),
        nullable=False,
    )
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    expires_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_type: Mapped[CertFileType | None] = mapped_column(
        postgresql.ENUM(CertFileType, name="cert_file_type", create_type=True),
        nullable=True,
    )
    audience_override: Mapped[list[Audience] | None] = mapped_column(
        postgresql.ARRAY(AUDIENCE_ENUM),
    )

    topic_tags: Mapped[list[TopicTag]] = relationship(
        secondary=certification_topic_tags, lazy="selectin"
    )
