"""Resume variants mapped to audiences. Always visible (no publishable mixin)."""

import enum

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDMixin


class ResumeVariant(enum.StrEnum):
    TECH = "tech"
    BUSINESS = "business"


class Resume(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    variant: Mapped[ResumeVariant] = mapped_column(
        postgresql.ENUM(ResumeVariant, name="resume_variant", create_type=True),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
