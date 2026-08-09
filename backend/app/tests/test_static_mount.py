from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

from app.app import create_app
from app.core.config import get_settings

INDEX_HTML = '<!doctype html><html><body><div id="root">admin-spa</div></body></html>'


@pytest.fixture()
def static_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[httpx.ASGITransport]:
    (tmp_path / "index.html").write_text(INDEX_HTML)
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('bundle');")
    monkeypatch.setenv("ADMIN_STATIC_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield httpx.ASGITransport(app=create_app())
    get_settings.cache_clear()


async def test_root_returns_spa_index(static_app: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=static_app) as client:
        response = await client.get("http://test/")
    assert response.status_code == 200
    assert response.text == INDEX_HTML


async def test_deep_route_returns_spa_index(static_app: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=static_app) as client:
        response = await client.get("http://test/login")
    assert response.status_code == 200
    assert response.text == INDEX_HTML


async def test_existing_static_file_served(static_app: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=static_app) as client:
        response = await client.get("http://test/assets/app.js")
    assert response.status_code == 200
    assert response.text == "console.log('bundle');"


async def test_api_v1_health_still_200(static_app: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=static_app) as client:
        response = await client.get("http://test/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_api_path_returns_404_not_index(static_app: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=static_app) as client:
        response = await client.get("http://test/api/v1/nonexistent")
    assert response.status_code == 404
    assert "root" not in response.text


async def test_path_traversal_blocked(static_app: httpx.ASGITransport) -> None:
    async with httpx.AsyncClient(transport=static_app) as client:
        response = await client.get("http://test/%2e%2e/%2e%2e/etc/passwd")
    assert response.status_code == 200
    assert response.text == INDEX_HTML


async def test_no_static_dir_keeps_api_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ADMIN_STATIC_DIR", str(tmp_path / "missing"))
    get_settings.cache_clear()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app())
        ) as client:
            health = await client.get("http://test/api/v1/health")
            root = await client.get("http://test/")
        assert health.status_code == 200
        assert root.status_code == 404
    finally:
        get_settings.cache_clear()
