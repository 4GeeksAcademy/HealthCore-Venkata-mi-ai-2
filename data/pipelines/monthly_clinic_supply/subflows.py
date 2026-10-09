"""Prefect subflows for Monthly Clinic Supply Performance (Part 3)."""

from __future__ import annotations

from datetime import date
from typing import Any

from prefect import flow

from .tasks import (
    extract_supply_events as extract_supply_events_task,
    load_monthly_clinic_supply_performance as load_monthly_clinic_supply_performance_task,
    transform_monthly_clinic_kpis as transform_monthly_clinic_kpis_task,
    write_eval_snapshot as write_eval_snapshot_task,
)


@flow(name="extract_clinic_supply_telemetry")
def extract_clinic_supply_telemetry(month_start: date) -> dict[str, Any]:
    """Extract accepted clinic supply events for one UTC month (Option A)."""
    return extract_supply_events_task(month_start)


@flow(name="transform_monthly_clinic_supply_kpis")
def transform_monthly_clinic_supply_kpis(
    extract_result: dict[str, Any],
    month_start: date,
) -> list[dict[str, Any]]:
    """Build Supply Cost, Consumption, Stockout, and Expiry Risk rows."""
    return transform_monthly_clinic_kpis_task(extract_result, month_start)


@flow(name="load_monthly_clinic_supply_performance")
def load_monthly_clinic_supply_performance_subflow(
    rows: list[dict[str, Any]],
) -> int:
    """Upsert reporting.monthly_clinic_supply_performance for the month."""
    return load_monthly_clinic_supply_performance_task(rows)


@flow(name="snapshot_monthly_clinic_supply_eval")
def snapshot_monthly_clinic_supply_eval(
    rows: list[dict[str, Any]],
    month_start: date,
) -> str:
    """Optional eval snapshot under data/eval/ (non-critical)."""
    return write_eval_snapshot_task(rows, month_start)
