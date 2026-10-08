"""Prefect flow: monthly clinic supply performance (Part 2 resilience)."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from prefect import flow, task
from prefect.tasks import task_input_hash

from .clinics import CLINIC_ALLOWLIST, FLOW_NAME
from .db import get_engine, init_reporting_schema
from .eval_snapshot import write_eval_snapshot as write_eval_snapshot_impl
from .extract import extract_month
from .load import load_monthly_clinic_supply_performance as load_impl
from .runs import begin_run, finish_run, update_run
from .transform import transform_monthly_clinic_kpis as transform_impl
from .transform import transform_stats

logger = logging.getLogger("healthcore.pipeline.monthly_clinic_supply")


def previous_utc_month(today: date | None = None) -> date:
    current = today or datetime.now(timezone.utc).date()
    first_this = current.replace(day=1)
    last_prev = first_this - timedelta(days=1)
    return last_prev.replace(day=1)


def parse_month_start(value: str | date | None) -> date:
    if value is None:
        return previous_utc_month()
    if isinstance(value, date):
        return value.replace(day=1)
    return date.fromisoformat(value[:10]).replace(day=1)


@task(name="extract_supply_events", retries=3, retry_delay_seconds=5)
def extract_supply_events(month_start: date) -> dict[str, Any]:
    # 3 retries / 5s: absorbs Supabase pooler blips and brief network drops on SELECT.
    return extract_month(month_start)


@task(
    name="transform_monthly_clinic_kpis",
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)
def transform_monthly_clinic_kpis(extract_result: dict[str, Any], month_start: date) -> list[dict[str, Any]]:
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


@flow(name=FLOW_NAME)
def monthly_clinic_supply_performance(
    month_start: str | date | None = None,
    trigger: str = "schedule",
) -> dict[str, Any]:
    """Main ETL: extract → transform → load. Optional eval snapshot cannot stop the flow."""
    target = parse_month_start(month_start)
    init_reporting_schema(get_engine())
    run_id = begin_run(target, trigger=trigger, engine=get_engine())

    try:
        update_run(run_id, {"phase": "extract"})
        extracted = extract_supply_events(target)
        update_run(
            run_id,
            {
                "phase": "transform",
                "records_extracted": extracted["records_extracted"],
                "records_deduped": extracted["records_deduped"],
                "duplicate_event_id_count": extracted["duplicate_event_id_count"],
                "records_rejected": extracted["records_rejected"],
                "source": extracted["source"],
            },
        )

        rows = transform_monthly_clinic_kpis(extracted, target)
        stats = transform_stats(extracted.get("events") or [])
        update_run(
            run_id,
            {
                "phase": "load",
                "distinct_clinic_count": stats["distinct_clinic_count"],
                "distinct_session_count": stats["distinct_session_count"],
                "distinct_request_id_count": stats["distinct_request_id_count"],
            },
        )

        loaded = load_monthly_clinic_supply_performance(rows)

        # Optional / non-critical: failure is logged; ETL still Completes.
        snapshot_state = write_eval_snapshot(rows, target, return_state=True)
        if snapshot_state.is_failed():
            logger.warning(
                "optional write_eval_snapshot failed run_id=%s month_start=%s",
                run_id,
                target.isoformat(),
            )

        finish_run(
            run_id,
            status="Completed",
            phase="load",
            records_extracted=extracted["records_extracted"],
            records_deduped=extracted["records_deduped"],
            duplicate_event_id_count=extracted["duplicate_event_id_count"],
            records_rejected=extracted["records_rejected"],
            records_loaded=loaded,
            distinct_clinic_count=stats["distinct_clinic_count"],
            distinct_session_count=stats["distinct_session_count"],
            distinct_request_id_count=stats["distinct_request_id_count"],
            source=extracted["source"],
        )
        return {
            "run_id": run_id,
            "month_start": target.isoformat(),
            "status": "Completed",
            "records_loaded": loaded,
            "clinic_count": len(CLINIC_ALLOWLIST),
            "source": extracted["source"],
        }
    except Exception as exc:
        finish_run(
            run_id,
            status="Failed",
            phase="load",
            error_message=str(exc)[:500],
        )
        raise


def trigger_monthly_clinic_supply_performance(
    month_start: str | date | None = None,
) -> dict[str, Any]:
    """Manual trigger used by POST /reporting/pipeline-runs."""
    return monthly_clinic_supply_performance(month_start=month_start, trigger="manual")
