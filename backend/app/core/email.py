"""Email delivery via Resend.

One client reused by OTP sign-in and (Phase 2) form notifications. Sends are
awaited before the caller may report success — a fire-and-forget send that
silently fails would lock the admin out with no signal. Codes and bodies are
never logged (conventions invariant 15).
"""

import asyncio
import logging

import resend

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when an email cannot be delivered."""


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
        await asyncio.to_thread(resend.Emails.send, payload)
    except Exception as exc:
        logger.error("email send failed: %s", exc.__class__.__name__)
        raise EmailSendError("Email delivery failed") from exc


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
