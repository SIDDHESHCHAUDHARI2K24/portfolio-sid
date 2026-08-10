"""Form submission Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FormSubmissionPublic(BaseModel):
    id: UUID
    form_type: str
    created_at: datetime


class FormSubmissionAdmin(BaseModel):
    id: UUID
    form_type: str
    payload: dict
    consent_given: bool
    consent_text: str
    submitter_email: str | None
    ip_address: str | None
    user_agent: str | None
    is_read: bool
    created_at: datetime


class FormSubmissionUpdate(BaseModel):
    is_read: bool | None = None
