"""Post-commit cache revalidation client (conventions invariant 8).

Call ``revalidate`` AFTER the commit, never inside a transaction:
revalidating a change that then rolls back publishes a lie. Failures log
at ERROR level with tags and status but never raise — the content is
saved and correct; only the cache is stale (silent failure here is the
"edits don't work" trap, so the log line must be loud).
"""

import logging
from collections.abc import Sequence

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5.0


async def revalidate(tags: Sequence[str]) -> None:
    """POST ``tags`` to the frontend revalidation webhook. Never raises."""
    if not tags:
        return
    settings = get_settings()
    url = f"{settings.next_public_base_url}/api/revalidate"
    tag_list = list(tags)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                json={"tags": tag_list},
                headers={"x-revalidation-secret": settings.revalidation_secret or ""},
            )
    except Exception:
        logger.error("revalidation request failed: tags=%s", tag_list, exc_info=True)
        return
    if response.status_code != 200:
        logger.error(
            "revalidation rejected: tags=%s status=%s", tag_list, response.status_code
        )
        return
    logger.info("revalidated tags=%s", tag_list)
