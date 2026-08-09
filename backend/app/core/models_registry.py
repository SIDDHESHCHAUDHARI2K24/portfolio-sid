"""Central import point for every ORM model.

Alembic's env.py imports this module so autogenerate sees all tables.
Adding a feature = adding one import line below (append, alphabetical,
never reorder existing lines). A forgotten line produces a silently
empty migration.
"""

from typing import Any

from app.core.models import Base, TopicTag

metadata = Base.metadata

# Feature model imports append below, one line per feature, alphabetical:
# from app.features.<name>.models import ...
from app.features.auth.models import LoginAttempt, OtpChallenge  # noqa: E402

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
    "Base",
    "LoginAttempt",
    "OtpChallenge",
    "TopicTag",
    "metadata",
    "publishables",
    "register_publishable",
]
