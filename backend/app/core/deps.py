"""Shared FastAPI dependencies.

Feature slices import dependencies from core only, never from each other.
"""

from app.core.database import get_session
from app.core.storage import StorageAdapter, get_storage

get_db = get_session


def get_storage_adapter() -> StorageAdapter:
    return get_storage()


__all__ = ["get_db", "get_storage_adapter"]
