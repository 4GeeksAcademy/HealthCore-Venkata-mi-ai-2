"""Pydantic responses for incident CSV analysis and incident lookups (not raw dicts)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

IncidentStatus = Literal["open", "closed", "discarded"]
IncidentCategory = Literal["APPOINTMENT", "BILLING", "CLINICAL", "FACILITIES", "IT", "WORKFORCE"]


class IncidentAnalyzeResponse(BaseModel):
    total_processed: int
    total_valid: int
    total_invalid: int
    invalid_by_type: dict[str, int]
    by_category: dict[str, int]
    by_status: dict[str, int]
    avg_satisfaction_closed: float | None
    closed_with_score_count: int


class IncidentRecord(BaseModel):
    """One incident as the incident manager exposes it. No patient identifier."""

    incident_id: str
    clinic_id: str
    country: str
    category: IncidentCategory
    status: IncidentStatus
    satisfaction_score: float | None
    source_file: str
    first_recorded_at: str
    updated_at: str


class IncidentListResponse(BaseModel):
    total: int
    items: list[IncidentRecord]


class IncidentCreate(BaseModel):
    """One incident. ``patient_id`` is stored and is never part of ``IncidentRecord``."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1, max_length=40)
    clinic_id: str = Field(min_length=1, max_length=40)
    country: str = Field(min_length=2, max_length=4)
    patient_id: str = Field(min_length=1, max_length=40)
    category: IncidentCategory
    status: IncidentStatus
    satisfaction_score: float | None = None


class IncidentStatusUpdate(BaseModel):
    """The only body ``PATCH /api/incidents/{id}/status`` accepts."""

    model_config = ConfigDict(extra="forbid")

    status: IncidentStatus
