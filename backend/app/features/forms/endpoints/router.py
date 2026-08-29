"""Form submission router: public POST (anti-abuse), admin inbox."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import FORMS
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.auth.utils import client_ip
from app.features.forms import service
from app.features.forms.models import FormType
from app.features.forms.schemas import (
    FormSubmissionAdmin,
    FormSubmissionUpdate,
)

GENERIC_SUCCESS = {"message": "Thank you for your submission."}

public_router = APIRouter(prefix="/api/v1/forms", tags=["forms"])
admin_router = APIRouter(
    prefix="/api/v1/admin/forms",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.post("/{form_type_str}", response_model=dict[str, str])
async def submit_form(
    form_type_str: str,
    request: Request,
    session: DbSession,
) -> dict[str, str]:
    if form_type_str not in {"contact", "dealflow"}:
        raise HTTPException(status_code=404, detail="Form type not found")

    form_type = FormType(form_type_str)

    body = None
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON") from exc

    # 1. Honeypot check
    honeypot = body.get("_hpt", "")
    if honeypot:
        return GENERIC_SUCCESS

    ip = client_ip(request)

    # 2. Rate limit (per-IP DB check: max 5 per IP per hour)
    rate_limit_ok = await _check_rate_limit(session, ip)
    if not rate_limit_ok:
        raise HTTPException(status_code=429, detail="Too many submissions. Please try again later.")

    # 3. Database write
    consent_given = bool(body.get("consent_given", False))
    consent_text = str(body.get("consent_text", ""))
    submitter_email = body.get("email") or None
    user_agent = request.headers.get("user-agent")

    payload = {
        k: v
        for k, v in body.items()
        if k
        not in {
            "_hpt",
            "consent_given",
            "consent_text",
            "email",
        }
    }

    await service.submit_dict(
        session,
        form_type=form_type,
        payload=payload,
        consent_given=consent_given,
        consent_text=consent_text,
        submitter_email=submitter_email,
        ip_address=ip,
        user_agent=user_agent,
    )

    return GENERIC_SUCCESS


async def _check_rate_limit(session: AsyncSession, ip: str) -> bool:
    """Max 5 submissions per IP per hour."""
    result = await session.execute(
        text(
            "SELECT COUNT(*) FROM form_submissions "
            "WHERE ip_address = :ip AND created_at > now() - interval '1 hour'"
        ),
        {"ip": ip},
    )
    count: int = result.scalar_one()
    return count < 5


@admin_router.get("", response_model=list[FormSubmissionAdmin])
async def list_admin(
    session: DbSession,
    form_type: str | None = None,
    is_read: str | None = None,
) -> list[FormSubmissionAdmin]:
    ft = FormType(form_type) if form_type else None
    ir = None
    if is_read is not None:
        ir = is_read.lower() == "true"
    items = await service.list_admin_dicts(session, form_type=ft, is_read=ir)
    return [FormSubmissionAdmin(**d) for d in items]


@admin_router.get("/{submission_id}", response_model=FormSubmissionAdmin)
async def get_admin(submission_id: str, session: DbSession) -> FormSubmissionAdmin:
    from uuid import UUID

    item = await service.get_dict(session, UUID(submission_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Form submission not found")
    return FormSubmissionAdmin(**item)


@admin_router.patch("/{submission_id}", response_model=FormSubmissionAdmin)
async def update_admin(
    submission_id: str, body: FormSubmissionUpdate, session: DbSession
) -> FormSubmissionAdmin:
    from uuid import UUID

    try:
        item = await service.update_dict(session, UUID(submission_id), body)
        await revalidate([FORMS])
        return FormSubmissionAdmin(**item)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.get("/export/csv", response_class=PlainTextResponse)
async def export_csv(
    session: DbSession,
    form_type: str | None = None,
) -> PlainTextResponse:
    ft = FormType(form_type) if form_type else None
    csv_data = await service.csv_export(session, form_type=ft)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=submissions.csv"},
    )
