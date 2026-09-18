"""Pydantic response for incident CSV analysis (not a raw dict)."""

from __future__ import annotations

from pydantic import BaseModel


class IncidentAnalyzeResponse(BaseModel):
    total_processed: int
    total_valid: int
    total_invalid: int
    invalid_by_type: dict[str, int]
    by_category: dict[str, int]
    by_status: dict[str, int]
    avg_satisfaction_closed: float | None
    closed_with_score_count: int
