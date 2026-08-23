"""Crawler analytics: which AI crawlers read what content.

Never stores raw IP addresses — only SHA-256 hashes. Middleware writes are
fire-and-forget to never block a response.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class CrawlerHit(Base):
    """One logged read by a known AI crawler."""

    __tablename__ = "crawler_hits"
    __table_args__ = (
        Index("ix_crawler_hits_timestamp", "timestamp"),
        Index("ix_crawler_hits_agent_label", "agent_label"),
    )

    id: Mapped[str] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(String(2000), nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
