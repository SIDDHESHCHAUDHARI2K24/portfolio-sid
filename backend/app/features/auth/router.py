"""Admin auth routes: password login, OTP verification, logout, admin/me."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.session import clear_session_cookie, set_session_cookie
from app.features.auth import service
from app.features.auth.schemas import LoginRequest, VerifyRequest

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1", tags=["auth"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=admin_auth())

DbSession = Annotated[AsyncSession, Depends(get_session)]


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, session: DbSession) -> dict[str, str]:
    detail = await service.request_otp(session, body.password, _client_ip(request))
    return {"detail": detail}


@router.post("/auth/verify")
@limiter.limit("10/minute")
async def verify(
    request: Request,
    body: VerifyRequest,
    response: Response,
    session: DbSession,
) -> dict[str, str]:
    token = await service.verify_otp(session, body.code, _client_ip(request))
    set_session_cookie(response, token)
    return {"status": "ok"}


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@admin_router.get("/me")
async def me() -> dict[str, str]:
    return {"status": "ok"}
