import httpx

from app.app import create_app


async def test_root_health() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app())) as client:
        response = await client.get("http://test/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_api_v1_health() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app())) as client:
        response = await client.get("http://test/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
