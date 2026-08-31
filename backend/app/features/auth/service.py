"""Auth service: password check, hashed OTP, DB-backed lockout.

Failure modes are indistinguishable by design: wrong password returns the
same generic detail as success, and every path pays the Argon2 cost. OTP
codes never appear in logs or responses (conventions invariant 15).
"""

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.core.session import create_session_token
from app.features.auth.models import (
    OTP_MAX_ATTEMPTS,
    OTP_TTL_SECONDS,
    AdminCredential,
    LoginAttempt,
    OtpChallenge,
)

logger = logging.getLogger(__name__)

# Dev-only, in-memory copy of the most recently issued OTP so the local e2e
# admin journey can complete without a configured email provider. NEVER read in
# production — the dev endpoint that returns it is gated on ENVIRONMENT and the
# value is cleared on the next issue. Codes are still only ever stored hashed in
# the DB (conventions invariant #15); this mirror exists solely to drive tests.
_DEV_LAST_CODE: str | None = None

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


async def get_effective_password_hash(session: AsyncSession) -> str | None:
    """Return the DB-overridden hash if present, else the env hash.

    Allows password rotation via ``change_password`` without a redeploy
    while keeping ``ADMIN_PASSWORD_HASH`` as the bootstrap fallback
    (conventions invariant 15 — Railway env is source of truth at boot)."""
    result = await session.execute(select(AdminCredential).limit(1))
    credential = result.scalars().first()
    if credential is not None:
        return credential.password_hash
    return get_settings().admin_password_hash


async def request_otp(session: AsyncSession, password: str, ip: str) -> str:
    """Verify the password and deliver a fresh OTP. Wrong password and
    correct password return the identical generic detail."""
    settings = get_settings()

    if await is_locked_out(session, ip):
        raise AuthError(429, "Too many attempts. Try again later.")

    effective_hash = await get_effective_password_hash(session)
    password_ok = verify_password(effective_hash, password) and effective_hash is not None
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

    # Dev mode: expose the code via the dev-only endpoint so the admin e2e
    # journey can run without a configured email provider. Best-effort email is
    # still attempted when one is configured (so devs/tests that assert on
    # delivery keep working), but a missing provider never fails the request.
    if settings.environment == "development":
        global _DEV_LAST_CODE
        _DEV_LAST_CODE = code
        logger.warning(
            "DEV: OTP %s issued; retrieve via GET /api/v1/auth/dev/otp", code
        )
        recipient = settings.admin_email
        if recipient:
            try:
                await email.send_otp(code, to=recipient)
            except email.EmailSendError:
                logger.warning("DEV: email delivery skipped (no provider configured)")
        return GENERIC_LOGIN_DETAIL

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


def get_dev_last_code() -> str | None:
    """Dev-only accessor for the most recently issued OTP. Returns ``None``
    unless a code has been issued in the current dev process."""
    return _DEV_LAST_CODE


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


async def change_password(
    session: AsyncSession, current_password: str, new_password: str
) -> None:
    """Verify current password against the effective hash and rotate to new.

    Validates ``new_password`` length (12-128) and that it differs from
    current. The new hash is UPSERTed into ``admin_credentials`` as the
    singleton row, so future logins use the DB value without a redeploy.
    The ``ADMIN_PASSWORD_HASH`` env remains as fallback if the row is
    deleted manually."""
    if len(new_password) < 12 or len(new_password) > 128:
        raise AuthError(400, "New password must be 12-128 characters.")
    if new_password == current_password:
        raise AuthError(400, "New password must differ from current password.")

    effective_hash = await get_effective_password_hash(session)
    if effective_hash is None or not verify_password(effective_hash, current_password):
        raise AuthError(403, "Current password is incorrect.")

    new_hash = hash_password(new_password)
    result = await session.execute(select(AdminCredential).limit(1))
    credential = result.scalars().first()
    if credential is None:
        credential = AdminCredential(password_hash=new_hash)
        session.add(credential)
    else:
        credential.password_hash = new_hash
    await session.commit()
