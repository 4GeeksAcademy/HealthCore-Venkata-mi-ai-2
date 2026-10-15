"""Create / update / query `job_runs` — status machine and processing lock."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .db import get_job_engine, init_job_runs_schema, is_sqlite

JOB_NAME_NIGHTLY_EXPORT = "nightly_export"

VALID_STATUSES = frozenset({"pending", "processing", "completed", "failed"})


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _stamp(value: datetime | None, sqlite: bool) -> Any:
    if value is None:
        return None
    return value.isoformat() if sqlite else value


def _date_param(value: date, sqlite: bool) -> Any:
    return value.isoformat() if sqlite else value


def create_pending(
    job_name: str,
    target_date: date,
    engine: Engine | None = None,
) -> str:
    """Insert a `pending` row before work begins. Returns run id."""
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    run_id = str(uuid4())
    sqlite = is_sqlite(eng)
    created = _now()
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO job_runs (
                  id, job_name, target_date, status,
                  started_at, finished_at, error_message, created_at
                ) VALUES (
                  :id, :job_name, :target_date, 'pending',
                  NULL, NULL, NULL, :created_at
                )
                """
            ),
            {
                "id": run_id,
                "job_name": job_name,
                "target_date": _date_param(target_date, sqlite),
                "created_at": _stamp(created, sqlite),
            },
        )
    return run_id


def mark_processing(run_id: str, engine: Engine | None = None) -> None:
    """Transition pending → processing (acquires the distributed lock)."""
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    sqlite = is_sqlite(eng)
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE job_runs
                SET status = 'processing',
                    started_at = :started_at,
                    error_message = NULL
                WHERE id = :id
                """
            ),
            {"id": run_id, "started_at": _stamp(_now(), sqlite)},
        )


def mark_completed(run_id: str, engine: Engine | None = None) -> None:
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    sqlite = is_sqlite(eng)
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE job_runs
                SET status = 'completed',
                    finished_at = :finished_at,
                    error_message = NULL
                WHERE id = :id
                """
            ),
            {"id": run_id, "finished_at": _stamp(_now(), sqlite)},
        )


def mark_failed(
    run_id: str,
    error_message: str,
    engine: Engine | None = None,
) -> None:
    """Any failure must land in `failed` — never leave a zombie `processing` row."""
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    sqlite = is_sqlite(eng)
    message = (error_message or "unknown_error")[:4000]
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE job_runs
                SET status = 'failed',
                    finished_at = :finished_at,
                    error_message = :error_message
                WHERE id = :id
                """
            ),
            {
                "id": run_id,
                "finished_at": _stamp(_now(), sqlite),
                "error_message": message,
            },
        )


def has_processing_lock(
    job_name: str = JOB_NAME_NIGHTLY_EXPORT,
    engine: Engine | None = None,
) -> bool:
    """True if any `processing` row exists for this job_name (distributed lock)."""
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    with eng.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id FROM job_runs
                WHERE job_name = :job_name AND status = 'processing'
                LIMIT 1
                """
            ),
            {"job_name": job_name},
        ).first()
    return row is not None


def has_completed_for_date(
    job_name: str,
    target_date: date,
    engine: Engine | None = None,
) -> bool:
    """Idempotency: completed run for (job_name, target_date) already exists."""
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    sqlite = is_sqlite(eng)
    with eng.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id FROM job_runs
                WHERE job_name = :job_name
                  AND target_date = :target_date
                  AND status = 'completed'
                LIMIT 1
                """
            ),
            {
                "job_name": job_name,
                "target_date": _date_param(target_date, sqlite),
            },
        ).first()
    return row is not None


def get_run_status(run_id: str, engine: Engine | None = None) -> str | None:
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    with eng.connect() as conn:
        row = conn.execute(
            text("SELECT status FROM job_runs WHERE id = :id"),
            {"id": run_id},
        ).first()
    return str(row[0]) if row else None
