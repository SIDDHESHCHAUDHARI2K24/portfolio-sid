"""Form submissions: one model for contact and dealflow with consent snapshots."""

import enum

from sqlalchemy import String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDMixin


class FormType(enum.StrEnum):
    CONTACT = "contact"
    DEALFLOW = "dealflow"


class FormSubmission(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "form_submissions"

    form_type: Mapped[FormType] = mapped_column(
        postgresql.ENUM(FormType, name="form_type", create_type=True),
        nullable=False,
    )
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSONB, nullable=False)
    consent_given: Mapped[bool] = mapped_column(default=False, server_default="false")
    consent_text: Mapped[str] = mapped_column(Text, nullable=False)
    submitter_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, server_default="false")
