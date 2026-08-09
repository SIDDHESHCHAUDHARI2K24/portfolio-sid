"""Shared FastAPI dependencies.

Feature slices import dependencies from core only, never from each other.
"""

from fastapi import HTTPException, Request
from fastapi.params import Depends

from app.core.access import verify_cf_access
from app.core.database import get_session
from app.core.session import COOKIE_NAME, read_session_token
from app.core.storage import StorageAdapter, get_storage

get_db = get_session


def get_storage_adapter() -> StorageAdapter:
    return get_storage()


def require_admin(request: Request) -> None:
    """401 unless a valid signed admin session cookie is present."""
    token = request.cookies.get(COOKIE_NAME)
    if token is None or read_session_token(token) is None:
        raise HTTPException(status_code=401, detail="Not authenticated")


def admin_auth() -> list[Depends]:
    """Router-level admin gate (conventions invariant 14): signed session
    cookie plus Cloudflare Access verification when enabled."""
    return [Depends(require_admin), Depends(verify_cf_access)]


__all__ = ["admin_auth", "get_db", "get_storage_adapter", "require_admin"]
