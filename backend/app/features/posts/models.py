"""Posts feature: external link and native (internal) entries routed to themed pages."""

import enum
from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, String, Table, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Audience
from app.core.models import (
    AUDIENCE_ENUM,
    Base,
    PublishableMixin,
    SortableMixin,
    TimestampMixin,
    TopicTag,
    UUIDMixin,
)


class PostPlatform(enum.StrEnum):
    SUBSTACK = "substack"
    MEDIUM = "medium"
    YOUTUBE = "youtube"
    OTHER = "other"
    INTERNAL = "internal"


class PostCollection(enum.StrEnum):
    TECH_RABBITHOLE = "tech_rabbithole"
    HOW_I_USE_AI = "how_i_use_ai"
    VC_FOR_FOUNDERS = "vc_for_founders"


POST_COLLECTION_ENUM = postgresql.ENUM(
    PostCollection,
    name="post_collection",
    create_type=True,
)


post_topic_tags = Table(
    "post_topic_tags",
    Base.metadata,
    Column(
        "post_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topic_tag_id",
        postgresql.UUID(as_uuid=True),
        ForeignKey("topic_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Post(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (
        # internal posts live on this site (slug + markdown body); every other
        # platform is an outbound link and needs a url. Labels are the enum
        # member NAMES (SQLAlchemy default), hence 'INTERNAL'.
        CheckConstraint(
            "(platform = 'INTERNAL' AND slug IS NOT NULL AND body IS NOT NULL) "
            "OR (platform <> 'INTERNAL' AND url IS NOT NULL)",
            name="ck_posts_platform_fields",
        ),
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    slug: Mapped[str | None] = mapped_column(String(200), unique=True, index=True)
    body: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[PostPlatform] = mapped_column(
        postgresql.ENUM(PostPlatform, name="post_platform", create_type=True),
        nullable=False,
    )
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    collections: Mapped[list[PostCollection]] = mapped_column(
        postgresql.ARRAY(POST_COLLECTION_ENUM),
        nullable=False,
        default=list,
        server_default="{}",
    )
    audience_override: Mapped[list[Audience] | None] = mapped_column(
        postgresql.ARRAY(AUDIENCE_ENUM),
    )

    topic_tags: Mapped[list[TopicTag]] = relationship(secondary=post_topic_tags, lazy="selectin")
