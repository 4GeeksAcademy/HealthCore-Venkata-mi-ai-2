"""SQLModel row for immutable telemetry_events (Supabase / test SQLite)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class TelemetryEventRow(SQLModel, table=True):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("ix_telemetry_events_timestamp", "timestamp"),
        Index("ix_telemetry_events_event_type", "event_type"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(nullable=False, index=False)
    service: str = Field(sa_column=Column(Text, nullable=False))
    event_type: str = Field(sa_column=Column(Text, nullable=False))
    level: str = Field(default="info", sa_column=Column(Text, nullable=False, server_default=text("'info'")))
    value: Decimal | None = Field(default=None, nullable=True)
    message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    tags: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(
            JSONB().with_variant(JSON(), "sqlite"),
            nullable=False,
            server_default=text("'{}'"),
        ),
    )
