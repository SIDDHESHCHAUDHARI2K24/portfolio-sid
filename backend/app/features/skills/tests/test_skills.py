"""Skills: API tests. Skills have no status, tags, or override logic."""

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.features.skills.endpoints import router as skills_router
from app.features.skills.models import Skill, SkillSection
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
async def clean_skills_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM skills"))


async def test_public_list_returns_all_skills(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_skills_tables: None,
) -> None:
    session.add_all(
        [
            Skill(name="Python", section=SkillSection.LANGUAGES, sort_order=1),
            Skill(name="TypeScript", section=SkillSection.LANGUAGES, sort_order=2),
            Skill(name="Docker", section=SkillSection.TOOLS, sort_order=1),
        ]
    )
    await session.commit()

    response = await client.get("http://test/api/v1/skills")
    assert response.status_code == 200
    data = response.json()
    names = [s["name"] for s in data]
    assert "Python" in names
    assert "TypeScript" in names
    assert "Docker" in names


async def test_public_list_ordered_by_section_subsection_sort(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_skills_tables: None,
) -> None:
    session.add_all(
        [
            Skill(name="B", section=SkillSection.TOOLS, sort_order=0),
            Skill(name="A", section=SkillSection.LANGUAGES, sort_order=0),
        ]
    )
    await session.commit()

    response = await client.get("http://test/api/v1/skills")
    data = response.json()
    sections = [s["section"] for s in data]
    assert sections[0] == "languages"
    assert sections[-1] == "tools"


async def test_skills_have_no_status_or_override_fields(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_skills_tables: None,
) -> None:
    session.add(Skill(name="Vim", section=SkillSection.TOOLS))
    await session.commit()

    response = await client.get("http://test/api/v1/skills")
    item = response.json()[0]
    assert "status" not in item
    assert "publish_at" not in item
    assert "audience_override" not in item
    assert "topic_tags" not in item


async def test_admin_routes_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/skills")).status_code == 401
    assert (
        await client.post(
            "http://test/api/v1/admin/skills",
            json={"name": "Figma", "section": "tools"},
        )
    ).status_code == 401


async def test_admin_crud_lifecycle(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_skills_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from collections.abc import Sequence

    async def fake_revalidate(tags: Sequence[str]) -> None:
        pass

    monkeypatch.setattr(skills_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/skills",
        json={"name": "React", "section": "frameworks", "sort_order": 1},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "React"
    assert created["section"] == "frameworks"

    skill_id = created["id"]

    update_resp = await client.patch(
        f"http://test/api/v1/admin/skills/{skill_id}",
        json={"name": "React 19", "subsection": "Frontend"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "React 19"
    assert update_resp.json()["subsection"] == "Frontend"

    delete_resp = await client.delete(f"http://test/api/v1/admin/skills/{skill_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/skills/{skill_id}")).status_code == 404


async def test_create_with_invalid_section_returns_422(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/skills",
        json={"name": "X", "section": "invalid_section"},
    )
    assert response.status_code == 422


async def test_revalidation_fires_after_create(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_skills_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from collections.abc import Sequence

    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(skills_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/skills",
        json={"name": "Go", "section": "languages"},
    )
    assert response.status_code == 201
    assert calls == [["skills"]]
