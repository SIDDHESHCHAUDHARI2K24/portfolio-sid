"""Collections feature: books, anime, manhwa. Personal-audience only.

No topic tags, no audience override.
"""

import enum

from sqlalchemy import String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, PublishableMixin, SortableMixin, TimestampMixin, UUIDMixin


class CollectionKind(enum.StrEnum):
    BOOK = "book"
    ANIME = "anime"
    MANHWA = "manhwa"


class CollectionStatus(enum.StrEnum):
    READING = "reading"
    COMPLETED = "completed"
    WANT_TO_READ = "want_to_read"


class ExternalSource(enum.StrEnum):
    OPEN_LIBRARY = "open_library"
    JIKAN = "jikan"
    MANUAL = "manual"


class CollectionItem(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    __tablename__ = "collection_items"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    creator: Mapped[str | None] = mapped_column(String(300), nullable=True)
    kind: Mapped[CollectionKind] = mapped_column(
        postgresql.ENUM(CollectionKind, name="collection_kind", create_type=True),
        nullable=False,
    )
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cover_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_source: Mapped[ExternalSource | None] = mapped_column(
        postgresql.ENUM(ExternalSource, name="external_source", create_type=True),
        nullable=True,
    )
    status_: Mapped[CollectionStatus | None] = mapped_column(
        postgresql.ENUM(CollectionStatus, name="collection_status", create_type=True),
        nullable=True,
        default=None,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
