"""Form submission service: orchestration, anti-abuse, notification."""

import csv
import io
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.core.config import get_settings
from app.features.forms import repository
from app.features.forms.models import FormSubmission, FormType
from app.features.forms.schemas import FormSubmissionUpdate

logger = logging.getLogger(__name__)


def _to_dict(sub: FormSubmission) -> dict[str, object]:
    return {
        "id": sub.id,
        "form_type": sub.form_type.value,
        "payload": sub.payload,
        "consent_given": sub.consent_given,
        "consent_text": sub.consent_text,
        "submitter_email": sub.submitter_email,
        "ip_address": sub.ip_address,
        "user_agent": sub.user_agent,
        "is_read": sub.is_read,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
    }


async def submit_dict(
    session: AsyncSession,
    form_type: FormType,
    payload: dict,
    consent_given: bool,
    consent_text: str,
    submitter_email: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> dict[str, object]:
    submission = FormSubmission(
        form_type=form_type,
        payload=payload,
        consent_given=consent_given,
        consent_text=consent_text,
        submitter_email=submitter_email,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    submission = await repository.create(session, submission)
    await session.commit()

    await _notify(submission)

    return _to_dict(submission)


async def _notify(submission: FormSubmission) -> None:
    settings = get_settings()
    recipient = settings.admin_email
    if not recipient or not settings.resend_api_key:
        logger.warning("Form notification skipped: admin_email or resend not configured")
        return

    type_label = "Contact" if submission.form_type == FormType.CONTACT else "Dealflow"
    payload_lines = "\n".join(f"  {k}: {v}" for k, v in submission.payload.items())
    try:
        await email.send_email(
            to=recipient,
            subject=f"[Portfolio] New {type_label} Submission",
            html=(
                f"<h2>New {type_label} Submission</h2>"
                f"<p><strong>Email:</strong> {submission.submitter_email or '—'}</p>"
                f"<p><strong>Consent:</strong> {'Yes' if submission.consent_given else 'No'}</p>"
                f"<pre>{payload_lines}</pre>"
                f"<p><em>IP: {submission.ip_address or '—'} | "
                f"UA: {submission.user_agent or '—'}</em></p>"
            ),
        )
    except Exception:
        logger.error(
            "Failed to send form notification email for submission %s",
            submission.id,
            exc_info=True,
        )


async def list_admin_dicts(
    session: AsyncSession,
    form_type: FormType | None = None,
    is_read: bool | None = None,
) -> list[dict[str, object]]:
    subs = await repository.list_all_admin(session, form_type=form_type, is_read=is_read)
    return [_to_dict(s) for s in subs]


async def get_dict(session: AsyncSession, submission_id: UUID) -> dict[str, object] | None:
    sub = await repository.get(session, submission_id)
    if sub is None:
        return None
    return _to_dict(sub)


async def update_dict(
    session: AsyncSession, submission_id: UUID, data: FormSubmissionUpdate
) -> dict[str, object]:
    sub = await repository.get(session, submission_id)
    if sub is None:
        raise ValueError("form submission not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub, key, value)

    sub.updated_at = datetime.now(UTC)
    await repository.update(session, sub)
    await session.commit()
    return _to_dict(sub)


async def csv_export(
    session: AsyncSession,
    form_type: FormType | None = None,
) -> str:
    subs = await repository.list_all_admin(session, form_type=form_type)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "form_type",
            "submitter_email",
            "consent_given",
            "consent_text",
            "is_read",
            "ip_address",
            "user_agent",
            "created_at",
            "payload",
        ]
    )
    for sub in subs:
        writer.writerow(
            [
                str(sub.id),
                sub.form_type.value,
                sub.submitter_email or "",
                sub.consent_given,
                sub.consent_text,
                sub.is_read,
                sub.ip_address or "",
                sub.user_agent or "",
                sub.created_at.isoformat() if sub.created_at else "",
                str(sub.payload),
            ]
        )
    return output.getvalue()
