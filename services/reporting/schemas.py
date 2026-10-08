"""Pydantic response models for /reporting routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PipelineRunLatest(BaseModel):
    run_id: str
    flow_name: str | None = None
    month_start: str | None = None
    trigger: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    status: str
    phase: str | None = None
    records_extracted: int = 0
    records_deduped: int = 0
    records_rejected: int = 0
    records_loaded: int = 0
    error_message: str | None = None
    source: str | None = None


class PipelineTriggerBody(BaseModel):
    month_start: str | None = None


class PipelineTriggerResponse(BaseModel):
    run_id: str
    month_start: str
    status: str
    records_loaded: int = 0
    source: str | None = None


class ClinicSupplyPerformance(BaseModel):
    clinic_id: str
    country: str
    total_supply_cost: float
    supply_consumption_count: int
    critical_stockout_count: int
    expiry_risk_count: int
    currency: str


class MonthlyClinicSupplyPerformanceResponse(BaseModel):
    month_start: str
    clinics: list[ClinicSupplyPerformance] = Field(default_factory=list)


class EmptyLatest(BaseModel):
    status: str = "none"
    detail: str = "No pipeline runs recorded yet."
    extras: dict[str, Any] = Field(default_factory=dict)
