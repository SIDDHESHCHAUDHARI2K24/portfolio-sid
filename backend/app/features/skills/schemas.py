"""Skills Pydantic schemas — no status/tags/override fields.

No ``from_attributes=True`` — ORM-to-dict conversion happens in the router
via ``_to_dict`` to avoid MissingGreenlet.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SkillPublic(BaseModel):
    id: UUID
    name: str
    section: str
    subsection: str | None
    icon_slug: str | None
    icon_key: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SkillAdmin(SkillPublic):
    pass


class SkillCreate(BaseModel):
    name: str
    section: str
    subsection: str | None = None
    icon_slug: str | None = None
    icon_key: str | None = None
    sort_order: int = 0


class SkillUpdate(BaseModel):
    name: str | None = None
    section: str | None = None
    subsection: str | None = None
    icon_slug: str | None = None
    icon_key: str | None = None
    sort_order: int | None = None
