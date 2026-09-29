"""Telemetry envelope models. TelemetryEvent is the Phase-2 contract — do not change fields."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    eventId: str
    timestamp: str
    sessionId: str
    userId: str | None = None
    event_type: str
    schemaVersion: str
    requestId: str
    properties: dict[str, Any] = Field(default_factory=dict)


class TelemetryBatchEnvelope(BaseModel):
    """Loose batch body: each item is validated with TelemetryEvent.model_validate in the handler."""

    events: list[Any]


class TelemetryReceived(BaseModel):
    received: int
    stored: int
    rejected: int
