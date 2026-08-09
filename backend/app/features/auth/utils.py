"""Feature-local helpers for the auth slice."""

from fastapi import Request


def client_ip(request: Request) -> str:
    """Best-effort client address for rate limiting and audit rows."""
    return request.client.host if request.client else "unknown"
