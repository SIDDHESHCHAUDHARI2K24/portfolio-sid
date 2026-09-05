"""contact items dynamic list

Revision ID: a605878385db
Revises: cc8619b8d037
Create Date: 2026-09-05 18:15:47.782642

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a605878385db'
down_revision: str | Sequence[str] | None = 'cc8619b8d037'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_EMAILS = (
    "s.chaudhari2k24@gmail.com",
    "s.chaudhari2k25@gmail.com",
    "siddheshcoursemail@gmail.com",
)

contact_profiles_table = sa.table(
    "contact_profiles",
    sa.column("id", sa.UUID()),
    sa.column("email", sa.String()),
    sa.column("linkedin_url", sa.String()),
    sa.column("linkedin_label", sa.String()),
    sa.column("cal_url", sa.String()),
    sa.column("cal_label", sa.String()),
    sa.column("github_url", sa.String()),
)

contact_items_table = sa.table(
    "contact_items",
    sa.column("id", sa.UUID()),
    sa.column("kind", sa.String()),
    sa.column("label", sa.String()),
    sa.column("url", sa.String()),
    sa.column("sort_order", sa.Integer()),
)


def upgrade() -> None:
    """Create contact_items, move fixed link columns into rows, seed the
    three public emails, then drop the fixed columns."""
    op.create_table(
        'contact_items',
        sa.Column('kind', sa.String(length=30), server_default='generic', nullable=False),
        sa.Column('label', sa.String(length=300), nullable=False),
        sa.Column('url', sa.String(length=2000), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    bind = op.get_bind()
    old_row = bind.execute(
        sa.select(
            contact_profiles_table.c.linkedin_url,
            contact_profiles_table.c.linkedin_label,
            contact_profiles_table.c.cal_url,
            contact_profiles_table.c.cal_label,
            contact_profiles_table.c.github_url,
        ).limit(1)
    ).first()

    rows: list[dict[str, object]] = [
        {
            "id": uuid.uuid4(),
            "kind": "email",
            "label": address,
            "url": f"mailto:{address}",
            "sort_order": index,
        }
        for index, address in enumerate(SEED_EMAILS)
    ]
    if old_row is not None:
        linkedin_url, linkedin_label, cal_url, cal_label, github_url = old_row
        legacy_rows = [
            {
                "id": uuid.uuid4(),
                "kind": "linkedin",
                "label": linkedin_label or "LinkedIn",
                "url": linkedin_url,
                "sort_order": len(SEED_EMAILS),
            },
            {
                "id": uuid.uuid4(),
                "kind": "cal",
                "label": cal_label or cal_url,
                "url": cal_url,
                "sort_order": len(SEED_EMAILS) + 1,
            },
            {
                "id": uuid.uuid4(),
                "kind": "github",
                "label": "GitHub",
                "url": github_url,
                "sort_order": len(SEED_EMAILS) + 2,
            },
        ]
        rows.extend(legacy_rows)

    if rows:
        op.bulk_insert(contact_items_table, rows)

    op.drop_column('contact_profiles', 'linkedin_url')
    op.drop_column('contact_profiles', 'email')
    op.drop_column('contact_profiles', 'linkedin_label')
    op.drop_column('contact_profiles', 'github_url')
    op.drop_column('contact_profiles', 'cal_url')
    op.drop_column('contact_profiles', 'cal_label')


def downgrade() -> None:
    """Re-add the fixed columns, backfill from contact_items, drop the table."""
    for column in (
        'linkedin_url',
        'email',
        'linkedin_label',
        'github_url',
        'cal_url',
        'cal_label',
    ):
        op.add_column(
            'contact_profiles', sa.Column(column, sa.String(), nullable=True)
        )

    bind = op.get_bind()
    email_row = bind.execute(
        sa.select(contact_items_table.c.url)
        .where(contact_items_table.c.kind == "email")
        .order_by(contact_items_table.c.sort_order)
        .limit(1)
    ).first()
    linkedin = bind.execute(
        sa.select(contact_items_table.c.url, contact_items_table.c.label)
        .where(contact_items_table.c.kind == "linkedin")
        .limit(1)
    ).first()
    cal = bind.execute(
        sa.select(contact_items_table.c.url, contact_items_table.c.label)
        .where(contact_items_table.c.kind == "cal")
        .limit(1)
    ).first()
    github = bind.execute(
        sa.select(contact_items_table.c.url)
        .where(contact_items_table.c.kind == "github")
        .limit(1)
    ).first()

    values: dict[str, str] = {
        "email": (
            email_row[0].removeprefix("mailto:") if email_row else "siddhesh@example.com"
        ),
        "linkedin_url": linkedin[0] if linkedin else "",
        "linkedin_label": linkedin[1] if linkedin else "LinkedIn",
        "cal_url": cal[0] if cal else "",
        "cal_label": cal[1] if cal else "",
        "github_url": github[0] if github else "",
    }
    bind.execute(
        contact_profiles_table.update().values(**values)
    )

    op.drop_table('contact_items')
    # ### end Alembic commands ###
