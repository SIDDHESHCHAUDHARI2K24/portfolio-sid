"""Central import point for every ORM model.

Alembic's env.py imports this module so autogenerate sees all tables.
Adding a feature = adding one import line below (append, alphabetical,
never reorder existing lines). A forgotten line produces a silently
empty migration.
"""

from app.core.models import Base

metadata = Base.metadata

# Feature model imports append below, one line per feature, alphabetical:
# from app.features.<name>.models import ...

__all__ = ["Base", "metadata"]
