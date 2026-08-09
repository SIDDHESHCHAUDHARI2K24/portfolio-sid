"""Request schemas for the auth endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    password: str


class VerifyRequest(BaseModel):
    code: str
