"""Request schemas for the auth endpoints."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str


class VerifyRequest(BaseModel):
    code: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        ..., min_length=1, description="Current admin password"
    )
    new_password: str = Field(
        ..., min_length=12, max_length=128, description="New password (12-128 chars)"
    )
