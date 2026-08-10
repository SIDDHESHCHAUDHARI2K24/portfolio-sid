"""Cover-fetching pipeline: Open Library for books, Jikan for anime/manga.

Download once, store in R2, never hotlink. Return structured result.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.storage import StorageAdapter, content_hashed_key

logger = logging.getLogger(__name__)

MAX_COVER_BYTES = 5 * 1024 * 1024
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
JIKAN_ANIME = "https://api.jikan.moe/v4/anime"
JIKAN_MANGA = "https://api.jikan.moe/v4/manga"

_negative_cache: dict[str, float] = {}
_NEGATIVE_TTL = 300


def _neg_cached(key: str) -> bool:
    ts = _negative_cache.get(key)
    if ts is None:
        return False
    if time.monotonic() - ts > _NEGATIVE_TTL:
        _negative_cache.pop(key, None)
        return False
    return True


def _neg_set(key: str) -> None:
    _negative_cache[key] = time.monotonic()
    if len(_negative_cache) > 100:
        oldest = min(_negative_cache, key=lambda k: _negative_cache[k])
        _negative_cache.pop(oldest, None)


@dataclass
class CoverResult:
    status: str  # "found" | "no_match" | "failed"
    cover_key: str | None = None


async def _download_image(url: str, client: httpx.AsyncClient) -> bytes | None:
    try:
        resp = await client.get(url, follow_redirects=True, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        logger.info("cover download failed url=%s err=%s", url, exc)
        return None

    ct = resp.headers.get("content-type", "")
    if not ct.startswith("image/"):
        logger.info("cover download non-image content-type=%s url=%s", ct, url)
        return None

    body = resp.content
    if len(body) > MAX_COVER_BYTES:
        logger.info("cover download too large size=%d url=%s", len(body), url)
        return None

    return body


def _extract_ol_image_url(data: dict[str, Any]) -> str | None:
    docs = data.get("docs", [])
    if not docs:
        return None
    cover_id = docs[0].get("cover_i")
    if cover_id:
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    return None


def _extract_jikan_image_url(data: dict[str, Any]) -> str | None:
    results = data.get("data", [])
    if not results:
        return None
    images = results[0].get("images", {})
    jpg = images.get("jpg", {})
    return jpg.get("image_url") or jpg.get("large_image_url")


async def _store_cover(adapter: StorageAdapter, body: bytes, prefix: str) -> str:
    if body.startswith(b"\x89PNG"):
        ext = "png"
    elif body.startswith(b"RIFF") and body[8:12] == b"WEBP":
        ext = "webp"
    else:
        ext = "jpg"
    key = content_hashed_key(prefix, body, ext)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, adapter.put, key, body, f"image/{ext}")
    return key


async def fetch_and_store_cover(
    title: str,
    kind: str,
    adapter: StorageAdapter,
    client: httpx.AsyncClient,
) -> CoverResult:
    """Look up ``title`` against the appropriate API, download the image,
    and store it in R2. Return a structured result."""

    if kind == "book":
        cache_key = f"ol:{title.lower()}"
        if _neg_cached(cache_key):
            return CoverResult(status="no_match")

        try:
            resp = await client.get(OPEN_LIBRARY_SEARCH, params={"title": title, "limit": "1"})
            resp.raise_for_status()
        except Exception as exc:
            logger.info("Open Library search failed title=%r err=%s", title, exc)
            return CoverResult(status="failed")

        image_url = _extract_ol_image_url(resp.json())
        prefix = "book"
    else:
        cache_key = f"jikan:{title.lower()}"
        if _neg_cached(cache_key):
            return CoverResult(status="no_match")

        endpoint = JIKAN_ANIME if kind == "anime" else JIKAN_MANGA
        try:
            resp = await client.get(endpoint, params={"q": title, "limit": "1"})
            resp.raise_for_status()
        except Exception as exc:
            logger.info("Jikan search failed title=%r endpoint=%s err=%s", title, endpoint, exc)
            return CoverResult(status="failed")

        image_url = _extract_jikan_image_url(resp.json())
        prefix = kind

    if not image_url:
        _neg_set(cache_key)
        return CoverResult(status="no_match")

    body = await _download_image(image_url, client)
    if body is None:
        return CoverResult(status="failed")

    key = await _store_cover(adapter, body, prefix)
    return CoverResult(status="found", cover_key=key)
