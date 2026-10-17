"""Anime/manhwa cover lookup: Jikan first, AniList fallback. No network."""

import json
from collections.abc import Callable

import httpx
import pytest

from app.core.storage import StorageAdapter
from app.features.collections import covers
from app.features.collections.covers import AniListError, fetch_and_store_cover

JPEG = b"\xff\xd8\xff\xe0" + b"x" * 64
JIKAN_IMG = "https://cdn.myanimelist.net/images/a.jpg"
ANILIST_IMG = "https://s4.anilist.co/file/a-large.jpg"


class FakeStorage(StorageAdapter):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = data

    def get_url(self, key: str) -> str:
        return f"http://test/{key}"

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self.objects


@pytest.fixture(autouse=True)
def _clear_negative_cache() -> None:
    covers._negative_cache.clear()


def _jikan_hit(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"data": [{"images": {"jpg": {"image_url": JIKAN_IMG}}}]})


def _jikan_miss(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"data": []})


def _jikan_timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("slow", request=request)


def _anilist_hit(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"data": {"Media": {"coverImage": {"extraLarge": ANILIST_IMG, "large": "x"}}}},
    )


def _anilist_null(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"data": {"Media": None}})


def _anilist_429(request: httpx.Request) -> httpx.Response:
    return httpx.Response(429, json={"errors": [{"message": "Too Many Requests"}]})


def _make_client(
    jikan: Callable[[httpx.Request], httpx.Response],
    anilist: Callable[[httpx.Request], httpx.Response],
    seen: list[httpx.Request],
) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        host = request.url.host
        if host == "api.jikan.moe":
            return jikan(request)
        if host == "graphql.anilist.co":
            return anilist(request)
        return httpx.Response(200, content=JPEG, headers={"content-type": "image/jpeg"})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _hosts(seen: list[httpx.Request]) -> list[str]:
    return [r.url.host for r in seen]


async def test_jikan_hit_uses_jikan_url() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_hit, _anilist_hit, seen) as client:
        result = await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    assert result.status == "found" and result.cover_key
    assert "graphql.anilist.co" not in _hosts(seen)
    assert "cdn.myanimelist.net" in _hosts(seen)


async def test_jikan_request_uses_short_timeout() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_hit, _anilist_hit, seen) as client:
        await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    jikan_req = next(r for r in seen if r.url.host == "api.jikan.moe")
    assert jikan_req.extensions["timeout"]["read"] == covers.JIKAN_TIMEOUT == 5


async def test_jikan_timeout_falls_back_to_anilist() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_timeout, _anilist_hit, seen) as client:
        result = await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    assert result.status == "found"
    assert "s4.anilist.co" in _hosts(seen)


async def test_jikan_no_match_falls_back_to_anilist() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_miss, _anilist_hit, seen) as client:
        result = await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    assert result.status == "found"
    assert "s4.anilist.co" in _hosts(seen)


async def test_both_miss_is_no_match_and_negative_cached() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_miss, _anilist_null, seen) as client:
        result = await fetch_and_store_cover("Nope", "anime", FakeStorage(), client)
        assert result.status == "no_match"
        calls = len(seen)
        again = await fetch_and_store_cover("Nope", "anime", FakeStorage(), client)
    assert again.status == "no_match"
    assert len(seen) == calls


async def test_jikan_error_and_anilist_null_is_failed_not_cached() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_timeout, _anilist_null, seen) as client:
        result = await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    assert result.status == "failed"
    assert not covers._negative_cache


async def test_both_error_is_failed_and_not_cached() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_timeout, _anilist_429, seen) as client:
        result = await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
        assert result.status == "failed"
        assert not covers._negative_cache
        calls = len(seen)
        await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    assert len(seen) > calls  # retried, no negative cache


async def test_anilist_429_is_not_retried() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_miss, _anilist_429, seen) as client:
        result = await fetch_and_store_cover("Naruto", "anime", FakeStorage(), client)
    assert result.status == "failed"
    assert _hosts(seen).count("graphql.anilist.co") == 1


async def test_anilist_query_types() -> None:
    for kind, expected in (("anime", "ANIME"), ("manhwa", "MANGA")):
        covers._negative_cache.clear()
        seen: list[httpx.Request] = []
        async with _make_client(_jikan_miss, _anilist_hit, seen) as client:
            await fetch_and_store_cover("Solo Leveling", kind, FakeStorage(), client)
        gql = next(r for r in seen if r.url.host == "graphql.anilist.co")
        payload = json.loads(gql.content)
        assert payload["variables"] == {"search": "Solo Leveling", "type": expected}
        assert "coverImage" in payload["query"]


async def test_anilist_image_goes_through_validation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.jikan.moe":
            return _jikan_miss(request)
        if request.url.host == "graphql.anilist.co":
            return _anilist_hit(request)
        return httpx.Response(200, content=b"<html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        store = FakeStorage()
        result = await fetch_and_store_cover("Naruto", "anime", store, client)
    assert result.status == "failed"
    assert not store.objects


async def test_books_never_touch_anilist() -> None:
    seen: list[httpx.Request] = []

    def ol(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"docs": []})

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return ol(request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_and_store_cover("Dune", "book", FakeStorage(), client)
    assert result.status == "no_match"
    assert _hosts(seen) == ["openlibrary.org"]


def test_anilist_error_is_exception() -> None:
    assert issubclass(AniListError, Exception)
