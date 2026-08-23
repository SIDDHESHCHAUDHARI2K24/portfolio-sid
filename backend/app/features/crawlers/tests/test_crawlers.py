"""Crawler: admin endpoint tests and middleware classification tests."""

import hashlib

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.features.crawlers.middleware import _classify_agent, _hash_ip
from app.features.crawlers.models import CrawlerHit
from app.tests.helpers import TEST_ADMIN_PASSWORD


async def _login(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []

    async def fake_send_otp(code: str, to: str) -> None:
        sent.append(code)

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    resp = await client.post(
        "http://test/api/v1/auth/login", json={"password": TEST_ADMIN_PASSWORD}
    )
    assert resp.status_code == 200
    resp = await client.post("http://test/api/v1/auth/verify", json={"code": sent[0]})
    assert resp.status_code == 200


@pytest_asyncio.fixture(loop_scope="session")
async def clean_crawler_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM crawler_hits"))


class TestAgentClassification:
    def test_classify_gptbot(self) -> None:
        assert _classify_agent("Mozilla/5.0 GPTBot/1.0") == "GPTBot"

    def test_classify_claude(self) -> None:
        assert _classify_agent("ClaudeBot/1.0") == "ClaudeBot"

    def test_classify_anthropic(self) -> None:
        assert _classify_agent("anthropic-ai/1.0") == "ClaudeBot"

    def test_classify_perplexity(self) -> None:
        assert _classify_agent("PerplexityBot/1.0") == "PerplexityBot"

    def test_classify_ccbot(self) -> None:
        assert _classify_agent("CCBot/2.0") == "CCBot"

    def test_classify_google_extended(self) -> None:
        assert _classify_agent("Google-Extended") == "Google-Extended"

    def test_classify_bytespider(self) -> None:
        assert _classify_agent("Bytespider") == "Bytespider"

    def test_classify_unknown(self) -> None:
        assert _classify_agent("Mozilla/5.0 Chrome/120") is None

    def test_classify_empty(self) -> None:
        assert _classify_agent("") is None

    def test_hash_ip(self) -> None:
        ip = "192.168.1.1"
        expected = hashlib.sha256(ip.encode()).hexdigest()
        assert _hash_ip(ip) == expected


class TestCrawlerAdminEndpoints:
    async def test_hits_requires_auth(self, client: httpx.AsyncClient) -> None:
        assert (await client.get("http://test/api/v1/admin/crawlers/hits")).status_code == 401

    async def test_summary_requires_auth(self, client: httpx.AsyncClient) -> None:
        assert (await client.get("http://test/api/v1/admin/crawlers/summary")).status_code == 401

    async def test_list_hits(
        self,
        client: httpx.AsyncClient,
        session: AsyncSession,
        clean_crawler_tables: None,
        clean_auth_tables: None,
        admin_settings: Settings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datetime import UTC, datetime

        await _login(client, monkeypatch)

        hit = CrawlerHit(
            user_agent="GPTBot/1.0",
            path="/posts/slug",
            ip_hash=_hash_ip("1.1.1.1"),
            agent_label="GPTBot",
            timestamp=datetime.now(UTC),
        )
        session.add(hit)
        await session.commit()

        resp = await client.get("http://test/api/v1/admin/crawlers/hits")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(h["agent_label"] == "GPTBot" for h in data)

    async def test_list_hits_filter_by_agent(
        self,
        client: httpx.AsyncClient,
        session: AsyncSession,
        clean_crawler_tables: None,
        clean_auth_tables: None,
        admin_settings: Settings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datetime import UTC, datetime

        await _login(client, monkeypatch)

        gpt_hit = CrawlerHit(
            user_agent="GPTBot/1.0",
            path="/posts/slug",
            ip_hash=_hash_ip("1.1.1.1"),
            agent_label="GPTBot",
            timestamp=datetime.now(UTC),
        )
        claude_hit = CrawlerHit(
            user_agent="ClaudeBot/1.0",
            path="/projects/slug",
            ip_hash=_hash_ip("2.2.2.2"),
            agent_label="ClaudeBot",
            timestamp=datetime.now(UTC),
        )
        session.add_all([gpt_hit, claude_hit])
        await session.commit()

        resp = await client.get("http://test/api/v1/admin/crawlers/hits?agent_label=GPTBot")
        assert resp.status_code == 200
        data = resp.json()
        assert all(h["agent_label"] == "GPTBot" for h in data)

    async def test_summary(
        self,
        client: httpx.AsyncClient,
        session: AsyncSession,
        clean_crawler_tables: None,
        clean_auth_tables: None,
        admin_settings: Settings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datetime import UTC, datetime

        await _login(client, monkeypatch)

        hit = CrawlerHit(
            user_agent="GPTBot/1.0",
            path="/posts/slug",
            ip_hash=_hash_ip("1.1.1.1"),
            agent_label="GPTBot",
            timestamp=datetime.now(UTC),
        )
        session.add(hit)
        await session.commit()

        resp = await client.get("http://test/api/v1/admin/crawlers/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert any(row["agent_label"] == "GPTBot" for row in data)

    async def test_hits_limit_enforced(
        self,
        client: httpx.AsyncClient,
        session: AsyncSession,
        clean_crawler_tables: None,
        clean_auth_tables: None,
        admin_settings: Settings,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from datetime import UTC, datetime

        await _login(client, monkeypatch)

        for i in range(5):
            hit = CrawlerHit(
                user_agent=f"GPTBot/{i}",
                path=f"/path/{i}",
                ip_hash=_hash_ip(f"10.0.0.{i}"),
                agent_label="GPTBot",
                timestamp=datetime.now(UTC),
            )
            session.add(hit)
        await session.commit()

        resp = await client.get("http://test/api/v1/admin/crawlers/hits?limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 3
