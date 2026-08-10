"""Certifications routers: public read-only, admin full CRUD."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_tags import CERTS
from app.core.database import get_session
from app.core.deps import admin_auth
from app.core.revalidation import revalidate
from app.features.certifications import service
from app.features.certifications.schemas import (
    CertificationAdmin,
    CertificationCreate,
    CertificationPublic,
    CertificationUpdate,
)

public_router = APIRouter(prefix="/api/v1/certifications", tags=["certifications"])
admin_router = APIRouter(
    prefix="/api/v1/admin/certifications",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@public_router.get("", response_model=list[CertificationPublic])
async def list_public(session: DbSession) -> list[CertificationPublic]:
    items = await service.list_public_dicts(session)
    return [CertificationPublic(**d) for d in items]


@public_router.get("/{cert_id}", response_model=CertificationPublic)
async def get_public(cert_id: UUID, session: DbSession) -> CertificationPublic:
    cert_dict = await service.get_dict(session, cert_id)
    if cert_dict is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    return CertificationPublic(**cert_dict)


@admin_router.get("", response_model=list[CertificationAdmin])
async def list_admin(session: DbSession) -> list[CertificationAdmin]:
    items = await service.list_admin_dicts(session)
    return [CertificationAdmin(**d) for d in items]


@admin_router.get("/{cert_id}", response_model=CertificationAdmin)
async def get_admin(cert_id: UUID, session: DbSession) -> CertificationAdmin:
    cert_dict = await service.get_dict(session, cert_id)
    if cert_dict is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    return CertificationAdmin(**cert_dict)


@admin_router.post("", response_model=CertificationAdmin, status_code=201)
async def create(body: CertificationCreate, session: DbSession) -> CertificationAdmin:
    try:
        cert_dict = await service.create_dict(session, body)
        await revalidate([CERTS])
        return CertificationAdmin(**cert_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.patch("/{cert_id}", response_model=CertificationAdmin)
async def update(
    cert_id: UUID, body: CertificationUpdate, session: DbSession
) -> CertificationAdmin:
    try:
        cert_dict = await service.update_dict(session, cert_id, body)
        await revalidate([CERTS])
        return CertificationAdmin(**cert_dict)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@admin_router.delete("/{cert_id}", status_code=204)
async def delete(cert_id: UUID, session: DbSession) -> None:
    try:
        await service.delete(session, cert_id)
        await revalidate([CERTS])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
