"""widen resume variant to string (D1 A)

Revision ID: 869fc8d8c856
Revises: 4d50231ae3d7
Create Date: 2026-08-30

D1 A — widen ``resumes.variant`` from native Postgres enum
``resume_variant`` (TECH/BUSINESS) to plain VARCHAR(50) with a
Python-level allowlist of 6 values (business, generic, vc,
ai_consultant, ai_workflow, product_engineer) per
``backend/scripts/resume_canon.json:resumes``.

Why String > native enum: ``docs/conventions.md`` invariant 7 —
Alembic cannot autogenerate ``ALTER TYPE ... ADD VALUE``, the DDL
cannot run inside a transaction, and dropping/renaming enum values
needs manual ``DROP TYPE``. A VARCHAR with validation in
``schemas.py``/``service.py`` keeps widening code-only.

Migration strategy
------------------
* ``USING LOWER(variant::text)`` normalises existing ``TECH``/
  ``BUSINESS`` rows to lower (``business`` stays valid, ``tech``
  becomes ``tech`` legacy; follow-up seed maps ``tech`` → ``generic``
  if desired).
* After the column is plain VARCHAR, the enum type is dropped
  (``DROP TYPE IF EXISTS resume_variant``) — safe on SQLite test DB
  where the type never existed. The drop is not strictly required for
  the column change but prevents future ``CREATE TYPE`` collisions and
  documents the intentional removal (manual enum note).
* Downgrade recreates the old 2-value enum and upper-cases strings;
  rows with the 4 new variants would fail the cast and must be
  manually reconciled — the downgrade is best-effort and intended for
  local rollback only.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "869fc8d8c856"
down_revision: str | Sequence[str] | None = "4d50231ae3d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Widen resumes.variant from native enum to VARCHAR(50)."""
    # Convert existing enum values to lower-case text as VARCHAR.
    # ``variant::text`` works for both enum and already-VARCHAR rows
    # (idempotent on re-run).
    op.execute(
        sa.text(
            "ALTER TABLE resumes ALTER COLUMN variant TYPE VARCHAR(50) "
            "USING LOWER(variant::text)"
        )
    )
    # Best-effort mapping for rollout: legacy ``tech`` → ``generic``
    # so the row immediately satisfies the new 6-value allowlist without
    # manual admin work. Keep ``business`` as-is (already valid).
    op.execute(sa.text("UPDATE resumes SET variant = 'generic' WHERE variant = 'tech'"))
    # Optionally drop the now-unused enum type. Not required for the
    # column change, but documents intentional removal per conventions 7.
    # ``IF EXISTS`` keeps this safe on SQLite / fresh DBs.
    op.execute(sa.text("DROP TYPE IF EXISTS resume_variant"))
    # Ensure the column is VARCHAR(50) even if autogenerate missed length.
    # This is a no-op if the previous ALTER TYPE already set it.
    op.alter_column(
        "resumes",
        "variant",
        existing_type=postgresql.ENUM("TECH", "BUSINESS", name="resume_variant"),
        type_=sa.String(length=50),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Best-effort revert to 2-value native enum (local rollback only)."""
    # Manual enum note: downgrade will fail if rows contain any of the
    # 4 new variants (ai_consultant, ai_workflow, vc, product_engineer)
    # or ``generic``. Reconcile those rows to ``TECH``/``BUSINESS``
    # before downgrading, or truncate resumes.
    op.execute(sa.text("UPDATE resumes SET variant = 'tech' WHERE variant = 'generic'"))
    # Recreate the old enum type
    resume_variant = postgresql.ENUM("TECH", "BUSINESS", name="resume_variant")
    resume_variant.create(op.get_bind(), checkfirst=True)
    op.execute(
        sa.text(
            "ALTER TABLE resumes ALTER COLUMN variant TYPE resume_variant "
            "USING UPPER(variant)::resume_variant"
        )
    )
