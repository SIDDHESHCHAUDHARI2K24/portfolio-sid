"""FastAPI middleware: log AI crawler visits as fire-and-forget records.

Never blocks the response. Only logs GET requests with a known bot
User-Agent pattern. IPs are hashed with SHA-256 — raw IPs are never stored.
"""

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import async_session_factory
from app.features.crawlers import repository
from app.features.crawlers.models import CrawlerHit

logger = logging.getLogger(__name__)

KNOWN_BOTS: dict[str, str] = {
    "GPTBot": "GPTBot",
    "ClaudeBot": "ClaudeBot",
    "claude": "ClaudeBot",
    "anthropic": "ClaudeBot",
    "PerplexityBot": "PerplexityBot",
    "CCBot": "CCBot",
    "Google-Extended": "Google-Extended",
    "Bytespider": "Bytespider",
}


def _classify_agent(user_agent: str) -> str | None:
    ua_lower = user_agent.lower()
    for pattern, label in KNOWN_BOTS.items():
        if pattern.lower() in ua_lower:
            return label
    return None


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()


async def _write_hit(
    factory: async_sessionmaker[AsyncSession],
    user_agent: str,
    path: str,
    ip_hash: str,
    agent_label: str,
) -> None:
    try:
        async with factory() as session:
            hit = CrawlerHit(
                user_agent=user_agent,
                path=path,
                ip_hash=ip_hash,
                agent_label=agent_label,
                timestamp=datetime.now(UTC),
            )
            await repository.create(session, hit)
            await session.commit()
    except Exception:
        logger.exception("crawler middleware: failed to write hit")


async def crawler_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response: Response = await call_next(request)

    if request.method != "GET":
        return response

    user_agent = request.headers.get("User-Agent", "")
    if not user_agent:
        return response

    agent_label = _classify_agent(user_agent)
    if agent_label is None:
        return response

    client_ip = request.client.host if request.client else "0.0.0.0"
    ip_hash = _hash_ip(client_ip)

    asyncio.ensure_future(
        _write_hit(
            async_session_factory,
            user_agent,
            str(request.url.path),
            ip_hash,
            agent_label,
        )
    )

    return response
