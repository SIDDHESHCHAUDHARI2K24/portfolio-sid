"""Seed-resumes helpers: hash determinism, idempotent upsert, variant allowlist.

Uses real Postgres (conventions: no DB mocks per docs/conventions.md).
Exposes helper imports via direct file load to avoid package-layout coupling.
"""

from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.features.resumes.models import ALLOWED_VARIANTS, Resume

# --- load seed_resumes helpers without relying on scripts being a package ---
_SEED_PATH = Path(__file__).resolve().parents[4] / "scripts" / "seed_resumes.py"
_spec = importlib.util.spec_from_file_location("seed_resumes", _SEED_PATH)
assert _spec and _spec.loader is not None  # type: ignore[truthy-bool]
_seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_seed)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# hash determinism
# ---------------------------------------------------------------------------


def test_content_hash_determinism_and_length() -> None:
    data = b"same-bytes-for-hash"
    h1 = _seed.content_hash(data)
    h2 = _seed.content_hash(data)
    assert h1 == h2
    assert len(h1) == 12
    # hex
    int(h1, 16)
    # different bytes -> different hash
    h3 = _seed.content_hash(b"different-bytes")
    assert h1 != h3


def test_content_hash_matches_sha256_prefix() -> None:
    data = b"abc123"
    expected = hashlib.sha256(data).hexdigest()[:12]
    assert _seed.content_hash(data) == expected


def test_resume_file_key_format() -> None:
    data = b"fake-pdf-bytes"
    for variant in sorted(ALLOWED_VARIANTS):
        key = _seed.resume_file_key(variant, data)
        assert key.startswith(f"resumes/{variant}-")
        assert key.endswith(".pdf")
        digest = key[len(f"resumes/{variant}-") : -len(".pdf")]
        assert len(digest) == 12
        int(digest, 16)


def test_resume_file_key_deterministic() -> None:
    data = b"deterministic-pdf"
    k1 = _seed.resume_file_key("business", data)
    k2 = _seed.resume_file_key("business", data)
    assert k1 == k2
    # different content -> different key
    k3 = _seed.resume_file_key("business", b"other")
    assert k1 != k3
    # different variant -> different key even for same bytes
    k4 = _seed.resume_file_key("generic", data)
    assert k1 != k4


def test_variant_allowlist_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="variant must be one of"):
        _seed.resume_file_key("invalid_variant", b"data")
    with pytest.raises(ValueError, match="variant must be one of"):
        _seed.resume_file_key("Business", b"data")  # case-sensitive
    with pytest.raises(ValueError, match="variant must be one of"):
        _seed.resume_file_key("tech", b"data")  # legacy, not in allowlist


# ---------------------------------------------------------------------------
# idempotent upsert — real DB
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(loop_scope="session")
async def clean_resumes_and_tags(db_engine: AsyncEngine):
    # session-scoped cleanup helper; tests that use it must also clean after
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))
        # keep topic_tags for other tests; only clean test slugs if any
    yield
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))


async def test_idempotent_resume_upsert_via_model(  # noqa: E501
    session: AsyncSession, db_engine: AsyncEngine
) -> None:
    """Direct model upsert by variant — seed logic idempotent (same key)."""
    # Clean slate for this test
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))

    data_a = b"pdf-version-one"
    variant = "business"
    key_a = _seed.resume_file_key(variant, data_a)
    # First insert
    row = Resume(variant=variant, label="Business / TPM", file_key=key_a, is_active=True)
    session.add(row)
    await session.commit()

    q = select(Resume).where(Resume.variant == variant)
    count1 = (await session.execute(q)).scalars().all()
    assert len(count1) == 1
    assert count1[0].file_key == key_a

    # Second upsert same variant same bytes -> same key (idempotent)
    existing = (await session.scalars(q)).first()
    assert existing is not None
    key_a2 = _seed.resume_file_key(variant, data_a)
    assert key_a2 == key_a
    existing.label = "Business / TPM"
    existing.file_key = key_a2
    await session.flush()
    await session.commit()

    count2 = (await session.execute(q)).scalars().all()
    assert len(count2) == 1
    assert count2[0].file_key == key_a

    # Third upsert different bytes -> new key, still one row
    data_b = b"pdf-version-two"
    key_b = _seed.resume_file_key(variant, data_b)
    assert key_b != key_a
    existing2 = (await session.scalars(q)).first()
    assert existing2 is not None
    existing2.file_key = key_b
    await session.flush()
    await session.commit()

    count3 = (await session.execute(q)).scalars().all()
    assert len(count3) == 1
    assert count3[0].file_key == key_b

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))
        # Re-create for other tests if needed? No, leave clean


async def test_idempotent_topic_tags_upsert(  # noqa: E501
    session: AsyncSession, db_engine: AsyncEngine
) -> None:
    """TopicTag upsert idempotent (second seed updates label)."""
    from app.core.models import TopicTag

    test_slug = "_test_seed_tag"
    # Ensure clean
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM topic_tags WHERE slug = :s"), {"s": test_slug})

    # First ensure
    _ = await _seed.ensure_topic_tags(  # noqa: E501
        session, [{"slug": test_slug, "label": "Test", "description": "d1"}], dry_run=False
    )
    await session.commit()
    rows = (await session.scalars(select(TopicTag).where(TopicTag.slug == test_slug))).all()
    assert len(rows) == 1
    assert rows[0].label == "Test"

    # Second run -> update, not duplicate
    _ = await _seed.ensure_topic_tags(  # noqa: E501
        session, [{"slug": test_slug, "label": "Test Updated", "description": "d1"}], dry_run=False
    )
    await session.commit()
    rows2 = (await session.scalars(select(TopicTag).where(TopicTag.slug == test_slug))).all()
    assert len(rows2) == 1
    assert rows2[0].label == "Test Updated"

    # Third run dry-run with changed description must not persist
    await _seed.ensure_topic_tags(
        session,
        [{"slug": test_slug, "label": "Test Updated", "description": "changed"}],
        dry_run=True,
    )
    # Dry-run should not have committed change
    await session.rollback()
    q = select(TopicTag).where(TopicTag.slug == test_slug)
    rows3 = (await session.scalars(q)).all()
    assert rows3[0].description == "d1"  # ensure still d1
    assert rows3[0].label == "Test Updated"

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM topic_tags WHERE slug = :s"), {"s": test_slug})
    await session.commit()


async def test_seed_resume_pdfs_idempotent_with_fake_pdf(  # noqa: E501
    session: AsyncSession, db_engine: AsyncEngine
) -> None:
    """Run seed_resume_pdfs twice with same fake PDF — count stays 1."""
    # Clean
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Create one fake PDF matching canon naming
        pdf_name = "Siddhesh Chaudhari Business Resume.pdf"
        pdf_path = tmp_path / pdf_name
        pdf_bytes = b"%PDF-1.4 fake-business-resume"
        pdf_path.write_bytes(pdf_bytes)

        canon_resumes = [
            {
                "variant": "business",
                "label": "Business / TPM Resume",
                "source_pdf": pdf_name,
                "is_active": True,
            }
        ]

        # Patch storage to avoid touching real filesystem/s3 during this unit test
        original_storage = _seed.get_storage

        mock_storage = MagicMock()
        mock_storage.put = MagicMock()
        mock_storage.get_url = MagicMock(return_value="http://example.com/media/resumes/business-abc.pdf")
        # Monkeypatch get_storage inside _seed module
        _seed.get_storage = lambda: mock_storage  # type: ignore[assignment]

        try:
            await _seed.seed_resume_pdfs(session, canon_resumes, tmp_path, dry_run=False)
            await session.commit()
            rows1 = (await session.scalars(select(Resume))).all()
            assert len(rows1) == 1
            file_key1 = rows1[0].file_key
            assert file_key1.startswith("resumes/business-")
            assert mock_storage.put.call_count == 1

            # Second run same bytes -> same key, still 1 row, put called again (idempotent storage)
            mock_storage.put.reset_mock()
            await _seed.seed_resume_pdfs(session, canon_resumes, tmp_path, dry_run=False)
            await session.commit()
            rows2 = (await session.scalars(select(Resume))).all()
            assert len(rows2) == 1
            assert rows2[0].file_key == file_key1
            assert mock_storage.put.call_count == 1

            # Dry-run must not change DB or call put
            mock_storage.put.reset_mock()
            await _seed.seed_resume_pdfs(session, canon_resumes, tmp_path, dry_run=True)
            # No commit — dry-run never writes
            rows3 = (await session.scalars(select(Resume))).all()
            assert len(rows3) == 1
            assert mock_storage.put.call_count == 0
        finally:
            _seed.get_storage = original_storage  # type: ignore[assignment]

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))
    await session.commit()


async def test_seed_rejects_unknown_variant_in_canon(  # noqa: E501
    session: AsyncSession,
) -> None:
    """seed_resume_pdfs raises for variant not in ALLOWED_VARIANTS."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "dummy.pdf").write_bytes(b"dummy")
        canon = [
            {  # noqa: E501
                "variant": "invalid_variant",
                "label": "X",
                "source_pdf": "dummy.pdf",
                "is_active": True,
            }
        ]
        with pytest.raises(ValueError, match="variant must be one of"):
            await _seed.seed_resume_pdfs(session, canon, tmp_path, dry_run=False)
