"""Resume variants mapped to audiences. Always visible (no publishable mixin).

Why ``String(50)`` and not a native Postgres enum
--------------------------------------------------
Postgres native enums require ``ALTER TYPE resume_variant ADD VALUE ...``
for every new variant. Alembic cannot autogenerate that DDL
(``docs/conventions.md`` invariant 7), it cannot run inside a
transaction block, and dropping/renaming values needs manual
``DROP TYPE`` handling. A plain ``VARCHAR(50)`` with a Python-level
allowlist keeps widening forward-compatible: adding a variant is a
code-only change (extend ``ALLOWED_VARIANTS`` + ``VARIANT_LABELS``),
validated in ``schemas.py``/``service.py`` without a new
``ALTER TYPE`` migration.
"""

import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDMixin

# Canonical 6 variants per ``backend/scripts/resume_canon.json:resumes``
# and ``docs/specs/resume-consolidation/PLAN.md`` D1 A.
ALLOWED_VARIANTS: frozenset[str] = frozenset(
    {
        "business",
        "generic",
        "vc",
        "ai_consultant",
        "ai_workflow",
        "product_engineer",
    }
)

# Human labels matching ``resume_canon.json`` (display names for admin/frontend).
VARIANT_LABELS: dict[str, str] = {
    "business": "Business / TPM",
    "generic": "Product Builder",
    "vc": "Venture Capital",
    "ai_consultant": "AI Consultant",
    "ai_workflow": "AI Workflow Engineer",
    "product_engineer": "Product Engineer",
}

# Legacy enum kept for backwards-compatible imports (e.g. older tests or
# ad-hoc scripts that did ``from app.features.resumes.models import ResumeVariant``).
# It is intentionally **not** bound to the DB column — the column is plain String.
# New code should use ``ALLOWED_VARIANTS`` / ``VARIANT_LABELS`` and plain ``str``.
class ResumeVariant(enum.StrEnum):
    BUSINESS = "business"
    GENERIC = "generic"
    VC = "vc"
    AI_CONSULTANT = "ai_consultant"
    AI_WORKFLOW = "ai_workflow"
    PRODUCT_ENGINEER = "product_engineer"
    # Deprecated legacy aliases — not valid for new writes, retained so
    # ``ResumeVariant.TECH`` imports do not crash during migration rollout.
    TECH = "tech"


class Resume(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    # Plain VARCHAR — see module docstring for rationale vs native PG enum.
    variant: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
