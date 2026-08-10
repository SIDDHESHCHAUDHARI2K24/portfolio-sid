"""Cloudflare Turnstile verification helper.

Reused by the form submission endpoint (E.T3) for bot protection.
"""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_TIMEOUT_SECONDS = 5.0


async def verify_turnstile(token: str, remoteip: str | None = None) -> bool:
    """POST to Cloudflare, check ``success`` field.

    Returns ``False`` on any failure — a failed verification is treated
    identically to an invalid token so bots learn nothing.
    """
    settings = get_settings()
    secret = settings.turnstile_secret_key
    if not secret:
        logger.error("TURNSTILE_SECRET_KEY not configured; rejecting token")
        return False

    payload: dict[str, str] = {"secret": secret, "response": token}
    if remoteip:
        payload["remoteip"] = remoteip

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=payload)
            data = response.json()
            return bool(data.get("success"))
    except Exception:
        logger.error("Turnstile verification request failed", exc_info=True)
        return False
