"""Admin auth routes: password login, OTP verification, logout, admin/me."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.session import clear_session_cookie, set_session_cookie
from app.features.auth import service
from app.features.auth.schemas import ChangePasswordRequest, LoginRequest, VerifyRequest
from app.features.auth.service import AuthError
from app.features.auth.utils import client_ip

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1", tags=["auth"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=admin_auth())

DbSession = Annotated[AsyncSession, Depends(get_session)]


@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, session: DbSession) -> dict[str, str]:
    detail = await service.request_otp(session, body.password, client_ip(request))
    return {"detail": detail}


@router.post("/auth/verify")
@limiter.limit("10/minute")
async def verify(
    request: Request,
    body: VerifyRequest,
    response: Response,
    session: DbSession,
) -> dict[str, str]:
    token = await service.verify_otp(session, body.code, client_ip(request))
    set_session_cookie(response, token)
    return {"status": "ok"}


@router.get("/auth/dev/otp")
async def dev_otp() -> dict[str, str]:
    """Dev-only: return the most recently issued OTP so the local e2e admin
    journey can log in without a configured email provider. Gated on
    ENVIRONMENT=development — returns 404 in every other mode so the endpoint
    is undetectable in production."""
    settings = get_settings()
    if settings.environment != "development":
        raise AuthError(404, "Not found")
    code = service.get_dev_last_code()
    if not code:
        raise AuthError(409, "No code issued yet")
    return {"code": code}


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@admin_router.get("/me")
async def me() -> dict[str, str]:
    return {"status": "ok"}


@admin_router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest, session: DbSession
) -> dict[str, str]:
    """Rotate the admin password. Authenticated via ``admin_auth`` (session cookie).

    Validates the current password, enforces 12-128 char policy on the new
    password (Pydantic + service double-check), and UPSERTs the new Argon2id
    hash into ``admin_credentials``. Future ``/auth/login`` calls check the
    DB row first (``get_effective_password_hash`` fallback). Use this after
    first login or whenever you want to rotate without a Railway redeploy."""
    await service.change_password(session, body.current_password, body.new_password)
    return {"status": "ok", "detail": "Password updated."}
