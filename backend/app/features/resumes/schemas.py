"""Resume Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResumePublic(BaseModel):
    id: UUID
    variant: str
    label: str
    file_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResumeAdmin(ResumePublic):
    pass


class ResumeCreate(BaseModel):
    variant: str
    label: str
    file_key: str
    is_active: bool = True


class ResumeUpdate(BaseModel):
    variant: str | None = None
    label: str | None = None
    file_key: str | None = None
    is_active: bool | None = None
