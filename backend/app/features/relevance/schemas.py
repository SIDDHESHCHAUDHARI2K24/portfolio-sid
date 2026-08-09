"""Relevance request/response schemas."""

from pydantic import BaseModel, field_validator

from app.core.enums import Audience

RelevanceMapResponse = dict[str, list[str]]

_AUDIENCE_VALUES = frozenset(a.value for a in Audience)


class AdminMapUpdate(BaseModel):
    mapping: dict[str, list[str]]

    @field_validator("mapping")
    @classmethod
    def audiences_must_be_valid(cls, mapping: dict[str, list[str]]) -> dict[str, list[str]]:
        unknown = sorted(key for key in mapping if key not in _AUDIENCE_VALUES)
        if unknown:
            raise ValueError(f"unknown audience values: {', '.join(unknown)}")
        return mapping
