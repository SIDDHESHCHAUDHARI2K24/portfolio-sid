"""Shared FastAPI dependencies.

Feature slices import dependencies from core only, never from each other.
"""

from app.core.database import get_session

get_db = get_session

__all__ = ["get_db"]
