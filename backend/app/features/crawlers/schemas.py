"""Crawler Pydantic schemas for the admin API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CrawlerHitOut(BaseModel):
    id: UUID
    user_agent: str
    path: str
    ip_hash: str
    agent_label: str | None
    timestamp: datetime


class CrawlerSummaryRow(BaseModel):
    agent_label: str | None
    week_start: str
    count: int
