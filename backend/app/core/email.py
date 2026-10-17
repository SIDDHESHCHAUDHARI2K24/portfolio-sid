"""Email delivery via Resend.

One client reused by OTP sign-in and (Phase 2) form notifications. Sends are
awaited before the caller may report success — a fire-and-forget send that
silently fails would lock the admin out with no signal. Codes and bodies are
never logged (conventions invariant 15).
"""

import asyncio
import logging
import re
from typing import Any

import resend

from app.core.config import get_settings

logger = logging.getLogger(__name__)


_EMAIL_RE = re.compile(r"\S+@\S+")
_KEY_RE = re.compile(r"\bre_\w+")
_MAX_MESSAGE_LEN = 200


class EmailSendError(Exception):
    """Raised when an email cannot be delivered."""


def _safe_message(exc: Exception) -> str:
    """Provider message with addresses redacted, truncated to 200 chars."""
    raw = getattr(exc, "message", None)
    text = raw if isinstance(raw, str) else str(exc)
    return _KEY_RE.sub("[redacted]", _EMAIL_RE.sub("[redacted]", text))[:_MAX_MESSAGE_LEN]


def _log_failure(exc: Exception) -> None:
    try:
        status = getattr(exc, "code", None)
        logger.error(
            "email send failed error=%s status=%s message=%s",
            exc.__class__.__name__,
            "none" if status is None else status,
            _safe_message(exc),
        )
    except Exception:  # logging must never mask the delivery error
        pass


def _log_success(response: Any, to: str) -> None:
    try:
        rid = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
        domain = to.rpartition("@")[2] or "none"
        logger.info("email sent id=%s to_domain=%s", rid or "none", domain)
    except Exception:
        pass


async def send_email(*, to: str, subject: str, html: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        logger.error("email send failed: RESEND_API_KEY not configured")
        raise EmailSendError("Email provider not configured")

    resend.api_key = settings.resend_api_key
    payload: resend.Emails.SendParams = {
        "from": settings.resend_from,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    try:
        response = await asyncio.to_thread(resend.Emails.send, payload)
    except Exception as exc:
        _log_failure(exc)
        raise EmailSendError("Email delivery failed") from exc
    _log_success(response, to)


async def send_otp(code: str, to: str) -> None:
    await send_email(
        to=to,
        subject="Your portfolio admin sign-in code",
        html=(
            f"<p>Your sign-in code is: <strong>{code}</strong></p>"
            "<p>It expires in 5 minutes. If you did not request it, "
            "someone has your password — change it.</p>"
        ),
    )
