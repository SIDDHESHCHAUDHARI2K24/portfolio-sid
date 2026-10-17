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


# --- download hardening: https only, host allowlist, redirects, streamed size cap ---


async def _download(handler: Callable[[httpx.Request], httpx.Response], url: str) -> bytes | None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        return await covers._download_image(url, client)


def _img(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=JPEG, headers={"content-type": "image/jpeg"})


async def test_download_allowed_hosts_ok() -> None:
    for url in (
        "https://covers.openlibrary.org/b/id/1-L.jpg",
        "https://cdn.myanimelist.net/images/a.jpg",
        "https://s4.anilist.co/file/a.jpg",
        "https://archive.org/download/x/y.jpg",
        "https://ia802809.us.archive.org/view_archive.php?file=y.jpg",
    ):
        assert await _download(_img, url) == JPEG, url


async def test_download_rejects_http() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _img(request)

    assert await _download(handler, "http://covers.openlibrary.org/b/id/1-L.jpg") is None
    assert seen == []


async def test_download_rejects_disallowed_host_without_request() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _img(request)

    for url in (
        "https://evil.example.com/a.jpg",
        "https://169.254.169.254/latest/meta-data",
        "https://covers.openlibrary.org.evil.com/a.jpg",
        "https://notarchive.org/a.jpg",
    ):
        assert await _download(handler, url) is None, url
    assert seen == []


async def test_download_redirect_to_disallowed_host_rejected_before_request() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "covers.openlibrary.org":
            return httpx.Response(302, headers={"location": "https://internal.example/secret"})
        return _img(request)

    assert await _download(handler, "https://covers.openlibrary.org/b/id/1-L.jpg") is None
    assert _hosts(seen) == ["covers.openlibrary.org"]


async def test_download_redirect_to_http_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "http://archive.org/a.jpg"})

    assert await _download(handler, "https://covers.openlibrary.org/b/id/1-L.jpg") is None


async def test_download_follows_open_library_redirect_chain() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "covers.openlibrary.org":
            return httpx.Response(302, headers={"location": "https://archive.org/download/a.jpg"})
        if request.url.host == "archive.org":
            return httpx.Response(
                302, headers={"location": "https://ia802809.us.archive.org/view.php?f=a.jpg"}
            )
        return _img(request)

    assert await _download(handler, "https://covers.openlibrary.org/b/id/1-L.jpg") == JPEG


async def test_download_max_three_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        n = int(request.url.params.get("n", "0"))
        if n < 4:
            return httpx.Response(302, headers={"location": f"https://archive.org/loop?n={n + 1}"})
        return _img(request)

    assert await _download(handler, "https://archive.org/loop?n=0") is None
    assert await _download(handler, "https://archive.org/loop?n=1") == JPEG  # 3 redirects ok


async def test_download_content_length_precheck_skips_body() -> None:
    class Boom(httpx.AsyncByteStream):
        async def __aiter__(self):  # type: ignore[no-untyped-def]
            raise AssertionError("body must not be read")
            yield b""  # pragma: no cover

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "content-type": "image/jpeg",
                "content-length": str(covers.MAX_COVER_BYTES + 1),
            },
            stream=Boom(),
        )

    assert await _download(handler, "https://s4.anilist.co/a.jpg") is None


async def test_download_oversized_stream_aborted_incrementally() -> None:
    chunk = b"x" * (1024 * 1024)
    yielded = 0

    class Endless(httpx.AsyncByteStream):
        async def __aiter__(self):  # type: ignore[no-untyped-def]
            nonlocal yielded
            for _ in range(100):  # no content-length: only the incremental cap can stop it
                yielded += 1
                yield chunk

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "image/png"}, stream=Endless())

    assert await _download(handler, "https://s4.anilist.co/a.png") is None
    assert yielded <= covers.MAX_COVER_BYTES // len(chunk) + 1


async def test_negative_cache_key_includes_kind() -> None:
    seen: list[httpx.Request] = []
    async with _make_client(_jikan_miss, _anilist_null, seen) as client:
        r1 = await fetch_and_store_cover("Same Title", "anime", FakeStorage(), client)
        assert r1.status == "no_match"
        n = len(seen)
        r2 = await fetch_and_store_cover("Same Title", "manhwa", FakeStorage(), client)
        assert r2.status == "no_match"
        assert len(seen) > n  # manhwa was actually looked up, not served from anime's cache
    assert "anime:same title" in covers._negative_cache
    assert "manhwa:same title" in covers._negative_cache
