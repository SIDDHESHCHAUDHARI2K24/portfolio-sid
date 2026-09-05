"""Contact content: a singleton profile (consent text) plus an ordered list
of contact items (emails, social links, booking links, phones...).

``ContactProfile`` is a fixed singleton (``singleton_guard`` unique constraint,
same pattern as ``auth.models.AdminCredentials``) holding page-level copy.
``ContactItem`` rows are the dynamic list the admin can add, remove, reorder,
and edit freely — order is ``sort_order``. Kinds drive the frontend icon
mapping; ``generic`` always renders with a fallback icon.
"""

import enum

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, SortableMixin, TimestampMixin, UUIDMixin


class ContactItemKind(enum.StrEnum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    X = "x"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    CAL = "cal"
    PHONE = "phone"
    WEBSITE = "website"
    GENERIC = "generic"


class ContactProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contact_profiles"

    consent_text: Mapped[str] = mapped_column(Text, nullable=False)
    singleton_guard: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", unique=True
    )


class ContactItem(UUIDMixin, TimestampMixin, SortableMixin, Base):
    __tablename__ = "contact_items"

    kind: Mapped[ContactItemKind] = mapped_column(
        String(30), nullable=False, server_default="generic"
    )
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
