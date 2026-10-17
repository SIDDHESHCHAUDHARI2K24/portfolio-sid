"""native posts: internal platform, slug and body (E03-W2)

Revision ID: 1d40cefb9666
Revises: a605878385db
Create Date: 2026-10-17

``ALTER TYPE ... ADD VALUE`` cannot be used in the same transaction as
statements that reference the new value (the CHECK below does), so it runs in
an ``autocommit_block`` that commits first. Enum labels are the Python member
NAMES (``INTERNAL``), matching the existing ``post_platform`` labels.

Downgrade drops the CHECK, the slug index and the slug/body columns and makes
``url`` NOT NULL again. The enum label stays in place (Postgres cannot drop
enum values). It refuses to run while internal rows exist: delete them first.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "1d40cefb9666"
down_revision: str | Sequence[str] | None = "a605878385db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECK_NAME = "ck_posts_platform_fields"


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE post_platform ADD VALUE IF NOT EXISTS 'INTERNAL'")

    op.add_column("posts", sa.Column("slug", sa.String(length=200), nullable=True))
    op.add_column("posts", sa.Column("body", sa.Text(), nullable=True))
    op.alter_column("posts", "url", existing_type=sa.String(length=2000), nullable=True)
    op.create_index(op.f("ix_posts_slug"), "posts", ["slug"], unique=True)
    op.create_check_constraint(
        CHECK_NAME,
        "posts",
        "(platform = 'INTERNAL' AND slug IS NOT NULL AND body IS NOT NULL) "
        "OR (platform <> 'INTERNAL' AND url IS NOT NULL)",
    )


def downgrade() -> None:
    internal = op.get_bind().execute(
        sa.text("SELECT count(*) FROM posts WHERE platform = 'INTERNAL'")
    )
    if internal.scalar_one():
        raise RuntimeError("Delete internal posts before downgrading (they have no url).")

    op.drop_constraint(CHECK_NAME, "posts", type_="check")
    op.drop_index(op.f("ix_posts_slug"), table_name="posts")
    op.alter_column("posts", "url", existing_type=sa.String(length=2000), nullable=False)
    op.drop_column("posts", "body")
    op.drop_column("posts", "slug")
