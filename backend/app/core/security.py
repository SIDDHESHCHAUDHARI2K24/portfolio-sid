"""Argon2id password hashing and verification.

The admin password hash lives only in ``ADMIN_PASSWORD_HASH`` (env). Every
failure path returns ``False`` — callers must never be able to distinguish
wrong-password from unknown-state in API responses or timing.
"""

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

_hasher = PasswordHasher()

_dummy_hash: str | None = None


def _timing_decoy_hash() -> str:
    """Verified against when no admin hash is configured, so the endpoint
    cost is identical whether or not a password exists."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = _hasher.hash("timing-decoy-not-a-password")
    return _dummy_hash


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _timing_decoy_hash(), password)
    except Argon2Error:
        return False
