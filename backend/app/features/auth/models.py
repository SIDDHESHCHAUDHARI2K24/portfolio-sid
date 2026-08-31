"""Auth models: hashed OTP challenges, DB-backed attempt log, admin credential override."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDMixin

OTP_MAX_ATTEMPTS = 5
OTP_TTL_SECONDS = 300
OTP_CODE_LENGTH = 6


class OtpChallenge(UUIDMixin, TimestampMixin, Base):
    """Single-use, short-lived OTP. Only the SHA-256 hash is stored; the
    code itself is never persisted, logged, or echoed."""

    __tablename__ = "otp_challenges"

    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_ip: Mapped[str | None] = mapped_column(String(45))


class LoginAttempt(Base):
    """Replica-safe lockout counter: IP, outcome, timestamp."""

    __tablename__ = "login_attempts"
    __table_args__ = (
        CheckConstraint("outcome IN ('success', 'failure')", name="ck_login_attempts_outcome"),
        Index("ix_login_attempts_ip_created_at", "ip", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    outcome: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AdminCredential(Base):
    """Singleton row holding the DB-overridden admin password hash.

    If no row exists the app falls back to ``ADMIN_PASSWORD_HASH`` env
    (``app.core.config``). When present this row is the effective
    credential, allowing password rotation via an authenticated endpoint
    without a redeploy. Only one row is ever active (enforced by a
    fixed ``singleton_guard`` unique constraint)."""

    __tablename__ = "admin_credentials"

    # Fixed singleton: application always uses ``singleton_guard = true``
    # so a unique partial constraint would work, but a simpler unique
    # on a constant boolean column suffices and keeps the migration
    # autogenerate clean.
    id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    singleton_guard: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", unique=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
