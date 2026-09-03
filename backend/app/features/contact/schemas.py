"""Contact Pydantic schemas."""

from pydantic import BaseModel


class ContactPublic(BaseModel):
    email: str
    linkedin_url: str
    linkedin_label: str
    cal_url: str
    cal_label: str
    github_url: str
    consent_text: str


class ContactAdmin(ContactPublic):
    pass


class ContactUpdate(BaseModel):
    email: str | None = None
    linkedin_url: str | None = None
    linkedin_label: str | None = None
    cal_url: str | None = None
    cal_label: str | None = None
    github_url: str | None = None
    consent_text: str | None = None
