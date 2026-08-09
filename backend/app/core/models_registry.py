"""Central import point for every ORM model.

Alembic's env.py imports this module so autogenerate sees all tables.
Adding a feature = adding one import line below (append, alphabetical,
never reorder existing lines). A forgotten line produces a silently
empty migration.
"""

from typing import Any

from app.core.cache_tags import OVERVIEW, TIMELINE
from app.core.models import Base, TopicTag

metadata = Base.metadata

# === APPEND-ZONE-START: feature model imports ===
# Add new feature model imports below, alphabetical, never reorder existing lines
from app.features.auth.models import LoginAttempt, OtpChallenge  # noqa: E402
from app.features.overview.models import OverviewIntro  # noqa: E402
from app.features.relevance.models import AudienceTagMap  # noqa: E402
from app.features.timeline.models import TimelineEntry  # noqa: E402
# === APPEND-ZONE-END: feature model imports ===

_PUBLISHABLES: list[tuple[type[Any], str]] = []


def register_publishable(model: type[Any], tag: str) -> None:
    """Register a publishable model for the scheduled-publish cron.

    APPEND-ONLY zone, same rules as the import block above: one line per
    feature, alphabetical, never reorder. Features register in Phase 1/2.
    The scheduler iterates this registry — a model that forgets to
    register never publishes on schedule.
    """
    _PUBLISHABLES.append((model, tag))


def publishables() -> list[tuple[type[Any], str]]:
    """Snapshot of registered ``(model, tag)`` pairs."""
    return list(_PUBLISHABLES)


__all__ = [
    "AudienceTagMap",
    "Base",
    "LoginAttempt",
    "OtpChallenge",
    "OverviewIntro",
    "TimelineEntry",
    "TopicTag",
    "metadata",
    "publishables",
    "register_publishable",
]

# === APPEND-ZONE-START: feature publishable registrations ===
# Add new feature publishable registrations below, alphabetical, never reorder
register_publishable(OverviewIntro, OVERVIEW)
register_publishable(TimelineEntry, TIMELINE)
# === APPEND-ZONE-END: feature publishable registrations ===
