"""Revalidation client: URL/header/payload contract; failures never raise."""

import logging
from typing import Any

import httpx
import pytest

from app.core import revalidation
from app.core.config import get_settings

SECRET = "test-revalidation-secret"
BASE_URL = "https://frontend.test"


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class FakeAsyncClient:
    """Records the request; configurable status or exception."""

    status_code: int = 200
    raise_exc: Exception | None = None
    requests: list[dict[str, Any]] = []
    init_kwargs: list[dict[str, Any]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        FakeAsyncClient.init_kwargs.append(kwargs)

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None

    async def post(
        self,
        url: str,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> FakeResponse:
        FakeAsyncClient.requests.append(
            {"url": url, "json": json, "headers": headers or {}}
        )
        if FakeAsyncClient.raise_exc is not None:
            raise FakeAsyncClient.raise_exc
        return FakeResponse(FakeAsyncClient.status_code)


@pytest.fixture(autouse=True)
def fake_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeAsyncClient.requests = []
    FakeAsyncClient.init_kwargs = []
    FakeAsyncClient.status_code = 200
    FakeAsyncClient.raise_exc = None
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    settings = get_settings()
    monkeypatch.setattr(settings, "revalidation_secret", SECRET)
    monkeypatch.setattr(settings, "next_public_base_url", BASE_URL)


async def test_revalidate_posts_contract() -> None:
    await revalidation.revalidate(["timeline", "overview"])

    assert len(FakeAsyncClient.requests) == 1
    request = FakeAsyncClient.requests[0]
    assert request["url"] == f"{BASE_URL}/api/revalidate"
    assert request["headers"]["x-revalidation-secret"] == SECRET
    assert request["json"] == {"tags": ["timeline", "overview"]}
    assert FakeAsyncClient.init_kwargs[0]["timeout"] == 5.0


async def test_revalidate_empty_tags_skips_request() -> None:
    await revalidation.revalidate([])
    assert FakeAsyncClient.requests == []


async def test_non_200_logs_error_and_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    FakeAsyncClient.status_code = 500

    with caplog.at_level(logging.ERROR, logger="app.core.revalidation"):
        await revalidation.revalidate(["timeline"])

    assert any("timeline" in record.message for record in caplog.records)
    assert any("500" in record.message for record in caplog.records)


async def test_connection_failure_logs_error_and_does_not_raise(
    caplog: pytest.LogCaptureFixture,
) -> None:
    FakeAsyncClient.raise_exc = httpx.ConnectError("connection refused")

    with caplog.at_level(logging.ERROR, logger="app.core.revalidation"):
        await revalidation.revalidate(["timeline"])

    assert any("timeline" in record.message for record in caplog.records)
