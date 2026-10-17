from pathlib import Path

import httpx
import pytest

from app.app import create_app
from app.core.config import get_settings
from app.core.storage import CACHE_CONTROL

HASHED = "book-0123456789ab.jpg"
HASHED_NESTED = "resumes/business-0123456789ab.pdf"
UNHASHED = "skills/python.svg"


@pytest.fixture()
def media_transport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> httpx.ASGITransport:
    for rel in (HASHED, HASHED_NESTED, UNHASHED):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"data")
    # Mutate the cached settings (conftest already does) instead of clearing the
    # cache, which would drop the admin password hash other tests rely on.
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_kind", "local")
    monkeypatch.setattr(settings, "local_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "admin_static_dir", str(tmp_path / "missing"))
    return httpx.ASGITransport(app=create_app())


def test_cache_control_constant_is_immutable_year() -> None:
    assert CACHE_CONTROL == "public, max-age=31536000, immutable"


@pytest.mark.parametrize("key", [HASHED, HASHED_NESTED])
async def test_hashed_media_is_immutable(media_transport: httpx.ASGITransport, key: str) -> None:
    async with httpx.AsyncClient(transport=media_transport) as client:
        response = await client.get(f"http://test/media/{key}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == CACHE_CONTROL


async def test_unhashed_media_gets_short_cache(media_transport: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=media_transport) as client:
        response = await client.get(f"http://test/media/{UNHASHED}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=300"


async def test_media_404_has_no_long_cache(media_transport: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=media_transport) as client:
        response = await client.get("http://test/media/book-ffffffffffff.jpg")
    assert response.status_code == 404
    assert "immutable" not in response.headers.get("cache-control", "")
    assert "max-age" not in response.headers.get("cache-control", "")


async def test_conditional_request_keeps_cache_header(
    media_transport: httpx.ASGITransport,
) -> None:
    async with httpx.AsyncClient(transport=media_transport) as client:
        first = await client.get(f"http://test/media/{HASHED}")
        second = await client.get(
            f"http://test/media/{HASHED}", headers={"if-none-match": first.headers["etag"]}
        )
    assert second.status_code == 304
    assert second.headers["cache-control"] == CACHE_CONTROL


async def test_api_responses_never_immutable(media_transport: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=media_transport) as client:
        response = await client.get("http://test/api/v1/health")
    assert "immutable" not in response.headers.get("cache-control", "")
