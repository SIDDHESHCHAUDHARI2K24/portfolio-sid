"""ProsePages feature: markdown pages with group routing, audience override, optional CTA."""

import enum

from sqlalchemy import String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import Audience
from app.core.models import (
    AUDIENCE_ENUM,
    Base,
    PublishableMixin,
    SortableMixin,
    TimestampMixin,
    UUIDMixin,
)


class ProseGroup(enum.StrEnum):
    HOBBIES = "hobbies"
    WORK_VIEWS = "work_views"
    INVESTOR_INTRO = "investor_intro"


class ProsePage(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    __tablename__ = "prose_pages"

    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    group: Mapped[ProseGroup] = mapped_column(
        postgresql.ENUM(ProseGroup, name="prose_group", create_type=True),
        nullable=False,
    )
    cta_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cta_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    audience_override: Mapped[list[Audience] | None] = mapped_column(
        postgresql.ARRAY(AUDIENCE_ENUM),
    )
