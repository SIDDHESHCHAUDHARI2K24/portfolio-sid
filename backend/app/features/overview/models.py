"""OverviewIntro model: per-audience headline/body/CTA.

One row per audience including a "default" row for crawlers and
first-time visitors. ``audience`` is a plain string column because
"default" must not enter the native Postgres audience enum (conventions
invariant 3, §4).
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, PublishableMixin, TimestampMixin, UUIDMixin

VALID_AUDIENCES = ("default", "recruiters", "techies", "investors", "founders", "personal")


class OverviewIntro(UUIDMixin, TimestampMixin, PublishableMixin, Base):
    """Per-audience introduction shown at the top of the homepage."""

    __tablename__ = "overview_intros"
    __table_args__ = (
        Index("ix_overview_intros_audience", "audience", unique=True),
        Index("ix_overview_intros_status_publish_at", "status", "publish_at"),
    )

    audience: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    headline: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hero_image_key: Mapped[str | None] = mapped_column(String(2000))
    cta_label: Mapped[str | None] = mapped_column(String(200))
    cta_url: Mapped[str | None] = mapped_column(String(2000))
