"""pipeline_runs audit helpers and concurrent-run lock."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .clinics import FLOW_NAME
from .db import get_engine, init_reporting_schema, is_sqlite, runs_table

STALE_RUNNING_MINUTES = 30


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _stamp(value: datetime | None, sqlite: bool) -> Any:
    if value is None:
        return None
    return value.isoformat() if sqlite else value


def close_stale_running(engine: Engine | None = None) -> None:
    eng = engine or get_engine()
    init_reporting_schema(eng)
    table = runs_table(eng)
    cutoff = _now() - timedelta(minutes=STALE_RUNNING_MINUTES)
    with eng.begin() as conn:
        conn.execute(
            text(
                f"""
                UPDATE {table}
                SET status = 'Failed',
                    ended_at = :ended_at,
                    error_message = 'stale_running',
                    phase = COALESCE(phase, 'extract')
                WHERE flow_name = :flow_name
                  AND status = 'Running'
                  AND started_at < :cutoff
                """
            ),
            {
                "ended_at": _stamp(_now(), is_sqlite(eng)),
                "flow_name": FLOW_NAME,
                "cutoff": _stamp(cutoff, is_sqlite(eng)),
            },
        )


def begin_run(
    month_start: date,
    trigger: str,
    engine: Engine | None = None,
) -> str:
    eng = engine or get_engine()
    init_reporting_schema(eng)
    close_stale_running(eng)
    table = runs_table(eng)
    run_id = str(uuid4())
    sqlite = is_sqlite(eng)
    with eng.begin() as conn:
        existing = conn.execute(
            text(
                f"""
                SELECT run_id FROM {table}
                WHERE flow_name = :flow_name
                  AND month_start = :month_start
                  AND status = 'Running'
                LIMIT 1
                """
            ),
            {
                "flow_name": FLOW_NAME,
                "month_start": month_start.isoformat() if sqlite else month_start,
            },
        ).first()
        if existing is not None:
            raise RuntimeError("pipeline_already_running")
        conn.execute(
            text(
                f"""
                INSERT INTO {table} (
                  run_id, flow_name, month_start, trigger, started_at,
                  ended_at, status, phase, records_extracted, records_loaded,
                  error_message, source
                ) VALUES (
                  :run_id, :flow_name, :month_start, :trigger, :started_at,
                  NULL, 'Running', 'extract', 0, 0, NULL, 'telemetry_events'
                )
                """
            ),
            {
                "run_id": run_id,
                "flow_name": FLOW_NAME,
                "month_start": month_start.isoformat() if sqlite else month_start,
                "trigger": trigger,
                "started_at": _stamp(_now(), sqlite),
            },
        )
    return run_id


def update_run(run_id: str, fields: dict[str, Any], engine: Engine | None = None) -> None:
    eng = engine or get_engine()
    table = runs_table(eng)
    sqlite = is_sqlite(eng)
    assignments = []
    params: dict[str, Any] = {"run_id": run_id}
    for key, value in fields.items():
        if key in {"started_at", "ended_at"} and isinstance(value, datetime):
            value = _stamp(value, sqlite)
        if key == "month_start" and isinstance(value, date):
            value = value.isoformat() if sqlite else value
        assignments.append(f"{key} = :{key}")
        params[key] = value
    if not assignments:
        return
    with eng.begin() as conn:
        conn.execute(
            text(f"UPDATE {table} SET {', '.join(assignments)} WHERE run_id = :run_id"),
            params,
        )


def finish_run(
    run_id: str,
    *,
    status: str,
    phase: str,
    error_message: str | None = None,
    engine: Engine | None = None,
    **metrics: Any,
) -> None:
    payload = {
        "status": status,
        "phase": phase,
        "ended_at": _now(),
        "error_message": error_message,
        **metrics,
    }
    update_run(run_id, payload, engine=engine)


def latest_pipeline_run(engine: Engine | None = None) -> dict[str, Any] | None:
    eng = engine or get_engine()
    init_reporting_schema(eng)
    table = runs_table(eng)
    try:
        with eng.connect() as conn:
            row = conn.execute(
                text(
                    f"""
                    SELECT run_id, flow_name, month_start, trigger, started_at, ended_at,
                           status, phase, records_extracted, records_deduped,
                           duplicate_event_id_count, records_rejected, records_loaded,
                           distinct_clinic_count, distinct_session_count,
                           distinct_request_id_count, error_message, source
                    FROM {table}
                    WHERE flow_name = :flow_name
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ),
                {"flow_name": FLOW_NAME},
            ).mappings().first()
    except SQLAlchemyError:
        return None
    if row is None:
        return None
    data = dict(row)
    for key in ("month_start", "started_at", "ended_at"):
        value = data.get(key)
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    data["run_id"] = str(data["run_id"])
    return data
