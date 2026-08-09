"""Relevance: pure resolver unit cases + real-Postgres map persistence.

Resolver cases run without a database (pure function, plain data). Map
persistence and endpoint tests run against the test Postgres — the
intersection logic is never mocked (conventions: tests never mock the
database for query-logic tests).
"""

from collections.abc import AsyncIterator, Sequence

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core import email
from app.core.config import Settings
from app.core.enums import DEFAULT_AUDIENCE, Audience
from app.core.models import TopicTag
from app.features.relevance import repository, service
from app.features.relevance.models import AudienceTagMap
from app.tests.helpers import TEST_ADMIN_PASSWORD

PUBLIC_MAP_URL = "http://test/api/v1/relevance/map"
ADMIN_MAP_URL = "http://test/api/v1/admin/relevance/map"
LOGIN_URL = "http://test/api/v1/auth/login"
VERIFY_URL = "http://test/api/v1/auth/verify"

TAG_MAP: dict[str, set[str]] = {
    "recruiters": {"engineering", "consulting"},
    "techies": {"ai", "engineering"},
    "investors": set(),
}


# --- pure resolver (no DB) -------------------------------------------------


def test_no_tags_not_relevant() -> None:
    assert service.is_relevant(set(), set(), "recruiters", TAG_MAP) is False


def test_tags_matching_one_audience_only() -> None:
    assert service.is_relevant({"consulting"}, set(), "recruiters", TAG_MAP) is True
    assert service.is_relevant({"consulting"}, set(), "techies", TAG_MAP) is False
    assert service.is_relevant({"consulting"}, set(), "investors", TAG_MAP) is False


def test_tags_matching_several_audiences() -> None:
    assert service.is_relevant({"engineering"}, set(), "recruiters", TAG_MAP) is True
    assert service.is_relevant({"engineering"}, set(), "techies", TAG_MAP) is True


def test_override_with_no_matching_tags() -> None:
    assert service.is_relevant({"knitting"}, {"investors"}, "investors", TAG_MAP) is True


def test_override_plus_matching_tags() -> None:
    assert service.is_relevant({"engineering"}, {"recruiters"}, "recruiters", TAG_MAP) is True


def test_empty_tag_map_for_audience() -> None:
    assert service.is_relevant({"startup"}, set(), "investors", TAG_MAP) is False
    # audience absent from the map entirely behaves the same
    assert service.is_relevant({"startup"}, set(), "founders", TAG_MAP) is False


def test_default_audience_highlights_nothing() -> None:
    assert DEFAULT_AUDIENCE not in TAG_MAP
    assert service.is_relevant({"engineering", "ai"}, set(), DEFAULT_AUDIENCE, TAG_MAP) is False


def test_override_containing_audience_forces_true_regardless_of_map() -> None:
    assert service.is_relevant(set(), {"founders"}, "founders", {}) is True
    assert service.is_relevant(set(), {"founders"}, "founders", TAG_MAP) is True


# --- fixtures ---------------------------------------------------------------


@pytest_asyncio.fixture(loop_scope="session")
async def clean_relevance_tables(db_engine: AsyncEngine) -> AsyncIterator[None]:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM audience_tag_map"))
        await conn.execute(text("DELETE FROM topic_tags"))
    yield


async def _create_tags(session: AsyncSession, *slugs: str) -> None:
    session.add_all(TopicTag(slug=slug, label=slug.capitalize()) for slug in slugs)
    await session.commit()


# --- repository against real Postgres ---------------------------------------


async def test_load_tag_map_shape(session: AsyncSession, clean_relevance_tables: None) -> None:
    await _create_tags(session, "engineering", "ai", "startup")
    await repository.replace_map(
        session,
        {"recruiters": ["engineering"], "techies": ["ai", "engineering"], "founders": ["startup"]},
    )
    await session.commit()

    tag_map = await repository.load_tag_map(session)
    assert tag_map == {
        "recruiters": {"engineering"},
        "techies": {"ai", "engineering"},
        "founders": {"startup"},
    }
    # unmapped audiences are simply absent — DEFAULT never appears
    assert "investors" not in tag_map
    assert DEFAULT_AUDIENCE not in tag_map


async def test_replace_map_old_rows_gone_new_present(
    session: AsyncSession, clean_relevance_tables: None
) -> None:
    await _create_tags(session, "engineering", "ai", "books")
    await repository.replace_map(session, {"recruiters": ["engineering"], "techies": ["ai"]})
    await session.commit()

    await repository.replace_map(session, {"personal": ["books"]})
    await session.commit()

    assert await repository.load_tag_map(session) == {"personal": {"books"}}


async def test_replace_map_unknown_slug_raises_before_writing(
    session: AsyncSession, clean_relevance_tables: None
) -> None:
    await _create_tags(session, "engineering")
    with pytest.raises(ValueError, match="unknown topic tag slugs"):
        await repository.replace_map(session, {"recruiters": ["engineering", "nope"]})
    await session.rollback()
    assert await repository.load_tag_map(session) == {}


async def test_duplicate_audience_tag_pair_rejected(
    session_factory: async_sessionmaker[AsyncSession], clean_relevance_tables: None
) -> None:
    async with session_factory() as session:
        tag = TopicTag(slug="ai", label="Ai")
        session.add(tag)
        await session.commit()

        session.add(AudienceTagMap(audience=Audience.TECHIES, topic_tag_id=tag.id))
        await session.commit()

        session.add(AudienceTagMap(audience=Audience.TECHIES, topic_tag_id=tag.id))
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


# --- endpoints ---------------------------------------------------------------


async def test_public_map_returns_200_json_and_cache_control(
    client: httpx.AsyncClient, clean_relevance_tables: None
) -> None:
    response = await client.get(PUBLIC_MAP_URL)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=300"
    payload = response.json()
    assert isinstance(payload, dict)
    # every real audience present, DEFAULT never exposed
    assert set(payload) == {a.value for a in Audience}
    assert DEFAULT_AUDIENCE not in payload


async def test_admin_map_requires_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(ADMIN_MAP_URL)).status_code == 401
    assert (
        await client.put(ADMIN_MAP_URL, json={"mapping": {"recruiters": ["engineering"]}})
    ).status_code == 401


async def _login(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Full auth flow with mocked email send (same pattern as test_auth)."""
    sent: list[tuple[str, str]] = []

    async def fake_send_otp(code: str, to: str) -> None:
        sent.append((code, to))

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 200
    response = await client.post(VERIFY_URL, json={"code": sent[0][0]})
    assert response.status_code == 200


async def test_admin_put_replaces_and_get_reflects(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_relevance_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _create_tags(session, "engineering", "ai", "startup")
    await _login(client, monkeypatch)

    response = await client.put(
        ADMIN_MAP_URL,
        json={"mapping": {"recruiters": ["engineering"], "techies": ["ai", "engineering"]}},
    )
    assert response.status_code == 200
    saved = response.json()
    assert saved["recruiters"] == ["engineering"]
    assert saved["techies"] == ["ai", "engineering"]
    # full matrix: empty audiences still present
    assert saved["founders"] == []
    assert set(saved) == {a.value for a in Audience}

    assert (await client.get(ADMIN_MAP_URL)).json() == saved
    assert (await client.get(PUBLIC_MAP_URL)).json() == saved


async def test_admin_put_invalid_audience_key_422(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    response = await client.put(ADMIN_MAP_URL, json={"mapping": {"aliens": ["ai"]}})
    assert response.status_code == 422


async def test_admin_put_unknown_slug_422(
    client: httpx.AsyncClient,
    clean_relevance_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    response = await client.put(ADMIN_MAP_URL, json={"mapping": {"recruiters": ["nope"]}})
    assert response.status_code == 422


async def test_admin_put_revalidates_relevance_tag_after_commit(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_relevance_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _create_tags(session, "engineering")
    await _login(client, monkeypatch)

    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(service, "revalidate", fake_revalidate)

    response = await client.put(ADMIN_MAP_URL, json={"mapping": {"recruiters": ["engineering"]}})
    assert response.status_code == 200
    assert calls == [["relevance"]]
