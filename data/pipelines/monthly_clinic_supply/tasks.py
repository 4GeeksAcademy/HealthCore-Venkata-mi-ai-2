"""Prefect tasks for the monthly clinic supply performance pipeline."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from prefect import task
from prefect.tasks import task_input_hash

from .db import get_engine
from .eval_snapshot import write_eval_snapshot as write_eval_snapshot_impl
from .extract import extract_month
from .load import load_monthly_clinic_supply_performance as load_impl
from .transform import transform_monthly_clinic_kpis as transform_impl


@task(name="extract_supply_events", retries=3, retry_delay_seconds=5)
def extract_supply_events(month_start: date) -> dict[str, Any]:
    # 3 retries / 5s: absorbs Supabase pooler blips and brief network drops on SELECT.
    return extract_month(month_start)


@task(
    name="transform_monthly_clinic_kpis",
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def transform_monthly_clinic_kpis(
    extract_result: dict[str, Any], month_start: date
) -> list[dict[str, Any]]:
    # Cache key = task_input_hash(extract_result, month_start): same deduped event set
    # and month reuse the KPI rows for up to one hour (ticket: skip repeat work).
    events = extract_result.get("events") or []
    return transform_impl(events, month_start)


@task(name="load_monthly_clinic_supply_performance", retries=3, retry_delay_seconds=5)
def load_monthly_clinic_supply_performance(rows: list[dict[str, Any]]) -> int:
    # 3 retries / 5s: upsert may hit pooler timeouts; recompute+upsert stays idempotent.
    return load_impl(rows, engine=get_engine())


@task(name="write_eval_snapshot", retries=0)
def write_eval_snapshot(rows: list[dict[str, Any]], month_start: date) -> str:
    return write_eval_snapshot_impl(rows, month_start)
