"""scripts/seed_demo.py: production guards and the never-touch-real-rows collection upsert."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.features.collections.models import CollectionItem, CollectionKind

_SEED_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py"
_spec = importlib.util.spec_from_file_location("seed_demo", _SEED_PATH)
assert _spec and _spec.loader is not None
seed: Any = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

LOCAL = "postgresql+asyncpg://u:p@localhost:5432/{db}"


@pytest.mark.parametrize(
    ("env", "url", "refused"),
    [
        ("development", LOCAL.format(db="portfolio_e03_demo"), False),
        ("local", "postgresql+asyncpg://u:p@127.0.0.1/portfolio", False),
        ("development", LOCAL.format(db="railway"), True),  # prod tunnelled to localhost
        ("development", LOCAL.format(db="Railway"), True),
        ("development", LOCAL.format(db="postgres"), True),
        ("development", LOCAL.format(db="myportfolio"), True),  # prefix, not substring
        ("development", "postgresql+asyncpg://u:p@localhost:5432", True),  # no db name
        ("production", LOCAL.format(db="portfolio"), True),
        ("development", "postgresql+asyncpg://u:p@db.example.com/portfolio", True),
    ],
)
def test_guard_problem(env: str, url: str, refused: bool) -> None:
    assert (seed.guard_problem(env, url) is not None) is refused


class _FakeSession:
    """Answers SELECT current_database() and records anything else as a write attempt."""

    def __init__(self, database: str | None) -> None:
        self.database = database
        self.other_calls: list[str] = []
        self.rolled_back = False

    async def scalar(self, stmt: Any) -> str | None:
        assert "current_database" in str(stmt)
        return self.database

    async def rollback(self) -> None:
        self.rolled_back = True

    async def scalars(self, *a: Any, **k: Any) -> Any:
        self.other_calls.append("scalars")

    def add(self, *a: Any, **k: Any) -> None:
        self.other_calls.append("add")

    async def delete(self, *a: Any, **k: Any) -> None:
        self.other_calls.append("delete")

    async def commit(self) -> None:
        self.other_calls.append("commit")


class _FakeFactory:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    def __call__(self) -> "_FakeFactory":
        return self

    async def __aenter__(self) -> _FakeSession:
        return self.session

    async def __aexit__(self, *exc: object) -> None:
        return None


@pytest.mark.parametrize("database", ["railway", "postgres", None])
@pytest.mark.parametrize("entry", ["seed", "remove"])
async def test_runtime_guard_refuses_before_any_write(
    database: str | None, entry: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _FakeSession(database)
    monkeypatch.setattr(seed, "async_session_factory", _FakeFactory(fake))
    with pytest.raises(SystemExit) as exc:
        if entry == "seed":
            await seed.seed(covers=False)
        else:
            await seed.remove()
    assert "refusing" in str(exc.value)
    assert fake.other_calls == []


async def test_runtime_guard_allows_portfolio_database(session: AsyncSession) -> None:
    await seed._guard_runtime(session)  # test DB is named portfolio_*


@pytest_asyncio.fixture(loop_scope="session")
async def clean_collection_items(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM collection_items"))


def _data(note: str) -> dict[str, Any]:
    return {"kind": CollectionKind.BOOK, "section": "s", "note": f"{note} {seed.MARKER}"}


async def test_collection_upsert_never_touches_unmarked_real_row(
    session: AsyncSession, clean_collection_items: None
) -> None:
    real = CollectionItem(title="Dune", kind=CollectionKind.BOOK, section="mine", note="my note")
    session.add(real)
    await session.commit()

    assert await seed._upsert_collection(session, "Dune", _data("sample")) is False
    await session.commit()

    rows = (
        await session.scalars(select(CollectionItem).where(CollectionItem.title == "Dune"))
    ).all()
    assert len(rows) == 1
    assert rows[0].note == "my note"
    assert rows[0].section == "mine"


async def test_collection_upsert_inserts_then_updates_marked_row(
    session: AsyncSession, clean_collection_items: None
) -> None:
    assert await seed._upsert_collection(session, "Dune", _data("v1")) is True
    await session.commit()
    assert await seed._upsert_collection(session, "Dune", _data("v2")) is True
    await session.commit()

    rows = (
        await session.scalars(select(CollectionItem).where(CollectionItem.title == "Dune"))
    ).all()
    assert len(rows) == 1
    assert rows[0].note == f"v2 {seed.MARKER}"


async def test_collection_upsert_updates_marked_even_if_unmarked_twin_exists(
    session: AsyncSession, clean_collection_items: None
) -> None:
    session.add(CollectionItem(title="Dune", kind=CollectionKind.BOOK, note="real"))
    session.add(CollectionItem(title="Dune", kind=CollectionKind.BOOK, note=f"old {seed.MARKER}"))
    await session.commit()

    assert await seed._upsert_collection(session, "Dune", _data("new")) is True
    await session.commit()

    notes = sorted(
        r.note or ""
        for r in (
            await session.scalars(select(CollectionItem).where(CollectionItem.title == "Dune"))
        ).all()
    )
    assert notes == sorted(["real", f"new {seed.MARKER}"])
