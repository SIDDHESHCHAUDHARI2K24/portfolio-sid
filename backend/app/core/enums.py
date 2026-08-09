"""Shared enums.

``DEFAULT_AUDIENCE`` is a Python-only sentinel for the uncategorised view.
It must NEVER become a database enum value: the database stores only real
audience segments, while "default" is a rendering concept (the variant
shown before any category is chosen), not content metadata.
"""

import enum


class Audience(enum.StrEnum):
    RECRUITERS = "recruiters"
    TECHIES = "techies"
    INVESTORS = "investors"
    FOUNDERS = "founders"
    PERSONAL = "personal"


DEFAULT_AUDIENCE = "default"


class PublishStatus(enum.StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
