"""Sanctioned query helpers (conventions invariant 8).

``public_filter`` is the ONLY sanctioned public read path: public endpoints
apply it, admin endpoints bypass it explicitly, and no endpoint may
reimplement the logic.
"""

from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.sql.elements import ColumnElement

from app.core.enums import PublishStatus


def public_filter(model: Any) -> ColumnElement[bool]:
    """Published rows, plus scheduled rows whose ``publish_at`` has passed."""
    return or_(
        model.status == PublishStatus.PUBLISHED,
        and_(model.status == PublishStatus.SCHEDULED, model.publish_at <= func.now()),
    )
