"""ContactProfile model: singleton row holding the public contact-page content.

One row ever (enforced by a fixed ``singleton_guard`` unique constraint, same
pattern as ``auth.models.AdminCredentials``). The migration seeds the row with
the values the frontend previously hardcoded, so the public API always has
data (conventions invariant 4: missing default row forbidden).
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDMixin


class ContactProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contact_profiles"

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    linkedin_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    linkedin_label: Mapped[str] = mapped_column(String(300), nullable=False)
    cal_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    cal_label: Mapped[str] = mapped_column(String(300), nullable=False)
    github_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    consent_text: Mapped[str] = mapped_column(Text, nullable=False)
    singleton_guard: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", unique=True
    )
