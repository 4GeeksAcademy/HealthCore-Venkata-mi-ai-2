"""Dead Letter Queue persistence for exhausted Celery retries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

try:
    from job_runner.db import get_job_engine, init_job_runs_schema, is_sqlite
except ImportError:  # pragma: no cover - package layout variants
    from services.job_runner.db import get_job_engine, init_job_runs_schema, is_sqlite


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def init_dlq_schema(engine=None) -> None:
    """Create `task_dead_letters` (separate from job_runs / pipeline_runs)."""
    eng = engine or get_job_engine()
    init_job_runs_schema(eng)
    with eng.begin() as conn:
        if is_sqlite(eng):
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS task_dead_letters (
                      id TEXT PRIMARY KEY,
                      task_id TEXT NOT NULL,
                      attempt INTEGER NOT NULL,
                      error_message TEXT NOT NULL,
                      created_at TEXT NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_task_dead_letters_task_id
                    ON task_dead_letters (task_id)
                    """
                )
            )
            return

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS task_dead_letters (
                  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                  task_id text NOT NULL,
                  attempt integer NOT NULL,
                  error_message text NOT NULL,
                  created_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_task_dead_letters_task_id
                ON task_dead_letters (task_id)
                """
            )
        )


def record_dead_letter(
    task_id: str,
    attempt: int,
    error_message: str,
    engine=None,
) -> dict[str, Any]:
    """Persist a DLQ row after max retries are exhausted."""
    eng = engine or get_job_engine()
    init_dlq_schema(eng)
    row_id = str(uuid.uuid4())
    created_at = _utcnow()
    message = (error_message or "unknown error")[:4000]
    with eng.begin() as conn:
        if is_sqlite(eng):
            conn.execute(
                text(
                    """
                    INSERT INTO task_dead_letters
                      (id, task_id, attempt, error_message, created_at)
                    VALUES
                      (:id, :task_id, :attempt, :error_message, :created_at)
                    """
                ),
                {
                    "id": row_id,
                    "task_id": task_id,
                    "attempt": int(attempt),
                    "error_message": message,
                    "created_at": created_at,
                },
            )
        else:
            conn.execute(
                text(
                    """
                    INSERT INTO task_dead_letters
                      (id, task_id, attempt, error_message, created_at)
                    VALUES
                      (CAST(:id AS uuid), :task_id, :attempt, :error_message, now())
                    """
                ),
                {
                    "id": row_id,
                    "task_id": task_id,
                    "attempt": int(attempt),
                    "error_message": message,
                },
            )
    return {
        "id": row_id,
        "task_id": task_id,
        "attempt": int(attempt),
        "error_message": message,
        "created_at": created_at,
    }


def list_dead_letters(task_id: str | None = None, engine=None) -> list[dict[str, Any]]:
    eng = engine or get_job_engine()
    init_dlq_schema(eng)
    with eng.connect() as conn:
        if task_id:
            rows = conn.execute(
                text(
                    """
                    SELECT id, task_id, attempt, error_message, created_at
                    FROM task_dead_letters
                    WHERE task_id = :task_id
                    ORDER BY created_at DESC
                    """
                ),
                {"task_id": task_id},
            ).mappings()
        else:
            rows = conn.execute(
                text(
                    """
                    SELECT id, task_id, attempt, error_message, created_at
                    FROM task_dead_letters
                    ORDER BY created_at DESC
                    LIMIT 100
                    """
                )
            ).mappings()
        return [dict(row) for row in rows]
