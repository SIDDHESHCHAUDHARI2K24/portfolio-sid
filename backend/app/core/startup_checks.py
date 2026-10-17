"""Fail-fast validation of auth-related config in production.

A missing hash or key otherwise fails silently (every login checks the timing
decoy; OTP email never sends) while the deploy still looks healthy. Messages
name variables only — never values, not even prefixes.
"""

import logging
import re

from argon2 import extract_parameters
from argon2.exceptions import Argon2Error

from app.core.config import Settings

logger = logging.getLogger(__name__)

_DEV_SESSION_SECRET = "dev-only-secret"
_SANDBOX_SENDER = "onboarding@resend.dev"
_MIN_SESSION_SECRET_LEN = 32
_EMAIL_RE = re.compile(r"[^@\s\"'<>,;]+@[^@\s\"'<>,;]+\.[^@\s\"'<>,;]+")
_QUOTES = "\"'`"


def _is_padded(value: str) -> bool:
    """Surrounding whitespace or quotes — the usual Railway paste error."""
    return value != value.strip() or value[:1] in _QUOTES or value[-1:] in _QUOTES


def _argon2_parses(value: str) -> bool:
    try:
        extract_parameters(value)
    except (Argon2Error, ValueError):
        return False
    return True


def validate_production_auth(settings: Settings) -> None:
    """Raise one ``RuntimeError`` naming every misconfigured auth variable.

    No-op outside production. Warnings (sandbox sender, empty proxy CIDRs) do
    not fail startup.
    """
    if settings.environment != "production":
        return

    failures: list[str] = []

    hash_value = settings.admin_password_hash
    if (
        not hash_value
        or _is_padded(hash_value)
        or not hash_value.startswith("$argon2id$")
        or not _argon2_parses(hash_value)
    ):
        failures.append("ADMIN_PASSWORD_HASH")

    secret = settings.session_secret
    if (
        not secret
        or _is_padded(secret)
        or secret == _DEV_SESSION_SECRET
        or len(secret) < _MIN_SESSION_SECRET_LEN
    ):
        failures.append("SESSION_SECRET")

    api_key = settings.resend_api_key
    if not api_key or _is_padded(api_key) or not api_key.startswith("re_"):
        failures.append("RESEND_API_KEY")

    email = settings.admin_email
    if not email or _is_padded(email) or not _EMAIL_RE.fullmatch(email):
        failures.append("ADMIN_EMAIL")

    sender = settings.resend_from
    if not sender or _is_padded(sender):
        failures.append("RESEND_FROM")
    elif sender == _SANDBOX_SENDER:
        logger.warning("RESEND_FROM is the Resend sandbox sender; delivery is owner-only")

    if not settings.trusted_proxy_cidrs:
        logger.warning(
            "TRUSTED_PROXY_CIDRS is empty; client IP falls back to the peer address, "
            "so lockout and rate limits are global"
        )

    if failures:
        message = "Invalid production auth configuration: " + ", ".join(failures)
        logger.error(message)
        raise RuntimeError(message)
