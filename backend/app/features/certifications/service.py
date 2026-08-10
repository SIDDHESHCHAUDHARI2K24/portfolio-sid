"""Certifications service: returns dicts (not ORM) to avoid MissingGreenlet."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Audience, PublishStatus
from app.core.models import TopicTag
from app.features.certifications import repository
from app.features.certifications.models import CertFileType, Certification, CertKind
from app.features.certifications.schemas import CertificationCreate, CertificationUpdate


def _cert_to_dict(cert: Certification) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": cert.id,
        "title": cert.title,
        "issuer": cert.issuer,
        "kind": _s(cert.kind),
        "issued_date": cert.issued_date,
        "expires_date": cert.expires_date,
        "credential_url": cert.credential_url,
        "file_key": cert.file_key,
        "file_type": _s(cert.file_type) if cert.file_type else None,
        "sort_order": cert.sort_order,
        "created_at": cert.created_at,
        "updated_at": cert.updated_at,
        "status": _s(cert.status),
        "publish_at": cert.publish_at,
        "published_at": cert.published_at,
        "audience_override": (
            [_s(a) for a in cert.audience_override] if cert.audience_override else None
        ),
        "topic_tags": [
            {"id": t.id, "slug": t.slug, "label": t.label} for t in (cert.topic_tags or [])
        ],
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    certs = await repository.list_public(session)
    return [_cert_to_dict(c) for c in certs]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    certs = await repository.list_admin(session)
    return [_cert_to_dict(c) for c in certs]


async def get_dict(session: AsyncSession, cert_id: UUID) -> dict[str, object] | None:
    cert = await repository.get(session, cert_id)
    if cert is None:
        return None
    return _cert_to_dict(cert)


async def _resolve_tags(session: AsyncSession, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    tags = list((await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all())
    found = {t.slug for t in tags}
    missing = set(slugs) - found
    if missing:
        raise ValueError(f"unknown topic tag slugs: {', '.join(sorted(missing))}")
    return [t.id for t in tags]


async def create_dict(session: AsyncSession, data: CertificationCreate) -> dict[str, object]:
    tag_ids = await _resolve_tags(session, data.tag_slugs)
    entry_data = data.model_dump(exclude={"tag_slugs"})

    raw_kind = entry_data["kind"]
    entry_data["kind"] = CertKind(raw_kind) if isinstance(raw_kind, str) else raw_kind

    raw_file_type = entry_data.get("file_type")
    if raw_file_type and isinstance(raw_file_type, str):
        entry_data["file_type"] = CertFileType(raw_file_type)

    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)
    if entry_data.get("audience_override"):
        entry_data["audience_override"] = [Audience(a) for a in entry_data["audience_override"]]

    cert = Certification(**entry_data)
    cert = await repository.create(session, cert, tag_ids)
    await session.commit()
    return _cert_to_dict(cert)


async def update_dict(
    session: AsyncSession, cert_id: UUID, data: CertificationUpdate
) -> dict[str, object]:
    cert = await repository.get(session, cert_id)
    if cert is None:
        raise ValueError("certification not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_slugs"})

    if update_data.get("kind") and isinstance(update_data["kind"], str):
        update_data["kind"] = CertKind(update_data["kind"])

    raw_file_type = update_data.get("file_type")
    if raw_file_type and isinstance(raw_file_type, str):
        update_data["file_type"] = CertFileType(raw_file_type)

    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and cert.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)
    if update_data.get("audience_override"):
        update_data["audience_override"] = [Audience(a) for a in update_data["audience_override"]]

    for key, value in update_data.items():
        setattr(cert, key, value)

    cert.updated_at = datetime.now(UTC)

    tag_ids = None
    if data.tag_slugs is not None:
        tag_ids = await _resolve_tags(session, data.tag_slugs)

    await repository.update(session, cert, tag_ids)
    await session.commit()
    return _cert_to_dict(cert)


async def delete(session: AsyncSession, cert_id: UUID) -> None:
    cert = await repository.get(session, cert_id)
    if cert is None:
        raise ValueError("certification not found")
    await repository.delete(session, cert)
    await session.commit()
