"""Contact Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, field_validator

from app.features.contact.models import ContactItemKind

ALLOWED_KINDS = sorted(k.value for k in ContactItemKind)


class ContactItemPublic(BaseModel):
    id: UUID
    kind: str
    label: str
    url: str
    sort_order: int


class ContactItemUpdate(BaseModel):
    id: UUID | None = None
    kind: str
    label: str
    url: str

    @field_validator("kind")
    @classmethod
    def _validate_kind(cls, v: str) -> str:
        if v not in ALLOWED_KINDS:
            allowed = ", ".join(ALLOWED_KINDS)
            raise ValueError(f"kind must be one of: {allowed} (got {v!r})")
        return v


class ContactPublic(BaseModel):
    consent_text: str
    items: list[ContactItemPublic]


class ContactAdmin(ContactPublic):
    pass


class ContactUpdate(BaseModel):
    consent_text: str | None = None
    items: list[ContactItemUpdate] | None = None
