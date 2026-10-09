"""API-facing trigger for the monthly clinic supply performance main flow."""

from __future__ import annotations

import importlib
from datetime import date
from typing import Any

from .dates import parse_month_start, previous_utc_month

__all__ = [
    "monthly_clinic_supply_performance",
    "parse_month_start",
    "previous_utc_month",
    "trigger_monthly_clinic_supply_performance",
]


def monthly_clinic_supply_performance(
    month_start: str | date | None = None,
    trigger: str = "schedule",
) -> dict[str, Any]:
    """Delegate to the main flow defined in data/pipelines/pipeline.py."""
    pipeline = importlib.import_module("pipeline")
    return pipeline.monthly_clinic_supply_performance(
        month_start=month_start,
        trigger=trigger,
    )


def trigger_monthly_clinic_supply_performance(
    month_start: str | date | None = None,
) -> dict[str, Any]:
    """Manual trigger used by POST /reporting/pipeline-runs."""
    return monthly_clinic_supply_performance(month_start=month_start, trigger="manual")
