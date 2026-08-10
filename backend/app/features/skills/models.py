"""Skills feature: one model grouped by section/subsection, no relevance logic.

Skills carry no status, tags, or audience override — everyone sees everything.
"""

import enum

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, SortableMixin, TimestampMixin, UUIDMixin


class SkillSection(enum.StrEnum):
    LANGUAGES = "languages"
    TOOLS = "tools"
    FRAMEWORKS = "frameworks"
    AI = "ai"
    BUSINESS = "business"


class Skill(UUIDMixin, TimestampMixin, SortableMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    section: Mapped[SkillSection] = mapped_column(
        postgresql.ENUM(SkillSection, name="skill_section", create_type=True),
        nullable=False,
    )
    subsection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    icon_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icon_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
