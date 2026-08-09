"""Auth service: password check, hashed OTP, DB-backed lockout.

Failure modes are indistinguishable by design: wrong password returns the
same generic detail as success, and every path pays the Argon2 cost. OTP
codes never appear in logs or responses (conventions invariant 15).
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.core.config import get_settings
from app.core.security import verify_password
from app.core.session import create_session_token
from app.features.auth.models import (
    OTP_MAX_ATTEMPTS,
    OTP_TTL_SECONDS,
    LoginAttempt,
    OtpChallenge,
)

GENERIC_LOGIN_DETAIL = "If the password is correct, a code has been sent."
GENERIC_OTP_DETAIL = "Invalid or expired code."
LOCKOUT_FAILURES = 10
LOCKOUT_WINDOW = timedelta(minutes=15)


class AuthError(Exception):
    """Service-level auth failure mapped to an HTTP status by app.py."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(UTC)


async def _record_attempt(session: AsyncSession, ip: str, outcome: str) -> None:
    session.add(LoginAttempt(ip=ip, outcome=outcome))


async def is_locked_out(session: AsyncSession, ip: str) -> bool:
    """>= LOCKOUT_FAILURES failures in the window. A success inside the
    window clears it: only failures after the last success count."""
    window_start = _utcnow() - LOCKOUT_WINDOW
    last_success = (
        await session.execute(
            select(func.max(LoginAttempt.created_at)).where(
                LoginAttempt.ip == ip,
                LoginAttempt.outcome == "success",
                LoginAttempt.created_at >= window_start,
            )
        )
    ).scalar_one()
    since = max(window_start, last_success) if last_success is not None else window_start
    failures = (
        await session.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.ip == ip,
                LoginAttempt.outcome == "failure",
                LoginAttempt.created_at >= since,
            )
        )
    ).scalar_one()
    return failures >= LOCKOUT_FAILURES


async def request_otp(session: AsyncSession, password: str, ip: str) -> str:
    """Verify the password and deliver a fresh OTP. Wrong password and
    correct password return the identical generic detail."""
    settings = get_settings()

    if await is_locked_out(session, ip):
        raise AuthError(429, "Too many attempts. Try again later.")

    password_ok = (
        verify_password(settings.admin_password_hash, password)
        and settings.admin_password_hash is not None
    )
    if not password_ok:
        await _record_attempt(session, ip, "failure")
        await session.commit()
        return GENERIC_LOGIN_DETAIL

    await _record_attempt(session, ip, "success")
    await session.execute(delete(OtpChallenge).where(OtpChallenge.consumed_at.is_(None)))

    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = OtpChallenge(
        code_hash=_hash_code(code),
        expires_at=_utcnow() + timedelta(seconds=OTP_TTL_SECONDS),
        created_ip=ip,
    )
    session.add(challenge)
    await session.commit()

    recipient = settings.admin_email
    if not recipient:
        await session.delete(challenge)
        await session.commit()
        raise AuthError(502, "Code delivery failed; try again later.")
    try:
        await email.send_otp(code, to=recipient)
    except email.EmailSendError as exc:
        await session.delete(challenge)
        await session.commit()
        raise AuthError(502, "Code delivery failed; try again later.") from exc

    return GENERIC_LOGIN_DETAIL


async def verify_otp(session: AsyncSession, code: str, ip: str) -> str:
    """Check the code against the latest outstanding challenge. Returns a
    fresh session token on success."""
    challenge = (
        await session.execute(
            select(OtpChallenge)
            .where(OtpChallenge.consumed_at.is_(None))
            .order_by(OtpChallenge.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if challenge is None:
        raise AuthError(400, GENERIC_OTP_DETAIL)
    if challenge.expires_at <= _utcnow():
        raise AuthError(400, "Code expired.")
    if challenge.attempts >= OTP_MAX_ATTEMPTS:
        raise AuthError(429, "Too many attempts. Request a new code.")

    if not hmac.compare_digest(_hash_code(code), challenge.code_hash):
        challenge.attempts += 1
        await session.commit()
        raise AuthError(400, GENERIC_OTP_DETAIL)

    challenge.consumed_at = _utcnow()
    await session.commit()
    return create_session_token()
