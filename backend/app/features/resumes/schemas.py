"""Resume Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.features.resumes.models import ALLOWED_VARIANTS


class ResumePublic(BaseModel):
    id: UUID
    variant: str
    label: str
    file_key: str
    file_url: str | None = None
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

    @field_validator("variant")
    @classmethod
    def _validate_variant(cls, v: str) -> str:
        if v not in ALLOWED_VARIANTS:
            allowed = ", ".join(sorted(ALLOWED_VARIANTS))
            raise ValueError(f"variant must be one of: {allowed} (got {v!r})")
        return v


class ResumeUpdate(BaseModel):
    variant: str | None = None
    label: str | None = None
    file_key: str | None = None
    is_active: bool | None = None

    @field_validator("variant")
    @classmethod
    def _validate_variant(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in ALLOWED_VARIANTS:
            allowed = ", ".join(sorted(ALLOWED_VARIANTS))
            raise ValueError(f"variant must be one of: {allowed} (got {v!r})")
        return v
