"""Unit tests for Ticket #DEV-53 nightly_export / job_runs."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.job_runner import (  # noqa: E402
    JOB_NAME_NIGHTLY_EXPORT,
    create_pending,
    has_completed_for_date,
    has_processing_lock,
    init_job_runs_schema,
    mark_completed,
    mark_failed,
    mark_processing,
    reset_job_engine,
)
from services.job_runner.db import get_job_engine, get_telemetry_engine  # noqa: E402
from services.job_runner.export import csv_path_for, export_telemetry_csv  # noqa: E402
from services.job_runner.service import get_run_status  # noqa: E402


@pytest.fixture()
def job_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "jobs.sqlite"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("JOB_RUNS_DATABASE_URL", url)
    monkeypatch.setenv("TELEMETRY_DATABASE_URL", url)
    reset_job_engine()
    eng = get_job_engine()
    init_job_runs_schema(eng)
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS telemetry_events (
                  id TEXT PRIMARY KEY,
                  timestamp TEXT NOT NULL,
                  service TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  level TEXT NOT NULL DEFAULT 'info',
                  value REAL,
                  message TEXT,
                  tags TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
        )
    yield eng
    reset_job_engine()


def _seed_event(eng, event_id: str, ts: str) -> None:
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO telemetry_events
                  (id, timestamp, service, event_type, level, value, message, tags)
                VALUES
                  (:id, :ts, 'backoffice', 'inbound_order_created', 'info', 1.0, null, '{}')
                """
            ),
            {"id": event_id, "ts": ts},
        )


def test_resolve_target_date_env_and_default():
    from scripts.nightly_export import resolve_target_date

    assert resolve_target_date({"TARGET_DATE": "2026-10-13"}) == date(2026, 10, 13)
    yesterday = datetime.now(timezone.utc).date()
    # default uses UTC yesterday — just ensure it is a date
    resolved = resolve_target_date({})
    assert isinstance(resolved, date)
    assert resolved <= yesterday


def test_processing_lock(job_db):
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is False
    run_id = create_pending(JOB_NAME_NIGHTLY_EXPORT, date(2026, 10, 13))
    mark_processing(run_id)
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is True
    mark_completed(run_id)
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is False


def test_idempotency_per_target_date(job_db):
    d1 = date(2026, 10, 13)
    d2 = date(2026, 10, 14)
    r1 = create_pending(JOB_NAME_NIGHTLY_EXPORT, d1)
    mark_processing(r1)
    mark_completed(r1)
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, d1) is True
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, d2) is False


def test_failure_never_leaves_processing(job_db):
    run_id = create_pending(JOB_NAME_NIGHTLY_EXPORT, date(2026, 10, 13))
    mark_processing(run_id)
    mark_failed(run_id, "boom")
    assert get_run_status(run_id) == "failed"
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is False


def test_csv_export_once(job_db, tmp_path: Path):
    _seed_event(job_db, "evt-1", "2026-10-13T12:00:00+00:00")
    raw = tmp_path / "raw"
    path, count, wrote = export_telemetry_csv(
        date(2026, 10, 13),
        engine=get_telemetry_engine(),
        raw_dir=raw,
    )
    assert wrote is True
    assert count == 1
    assert path.name == "telemetry_2026-10-13.csv"
    assert path.is_file()
    path2, count2, wrote2 = export_telemetry_csv(
        date(2026, 10, 13),
        engine=get_telemetry_engine(),
        raw_dir=raw,
    )
    assert wrote2 is False
    assert count2 == 0
    assert path2 == path
    text_body = path.read_text(encoding="utf-8")
    assert "inbound_order_created" in text_body
    assert "evt-1" in text_body


def test_nightly_export_skip_duplicate_and_lock(job_db, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from scripts import nightly_export as ne

    raw = tmp_path / "raw"
    monkeypatch.setenv("NIGHTLY_SKIP_PIPELINE", "1")
    monkeypatch.setattr(ne, "export_telemetry_csv", lambda *a, **k: (raw / "telemetry_2026-10-13.csv", 0, True))

    # First run completes
    code = ne.run_nightly_export(env={"TARGET_DATE": "2026-10-13", "NIGHTLY_SKIP_PIPELINE": "1"})
    assert code == 0
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, date(2026, 10, 13))

    # Second run skips as duplicate
    code2 = ne.run_nightly_export(env={"TARGET_DATE": "2026-10-13", "NIGHTLY_SKIP_PIPELINE": "1"})
    assert code2 == 0

    # Simulate lock held
    locked = create_pending(JOB_NAME_NIGHTLY_EXPORT, date(2026, 10, 15))
    mark_processing(locked)
    code3 = ne.run_nightly_export(env={"TARGET_DATE": "2026-10-14", "NIGHTLY_SKIP_PIPELINE": "1"})
    assert code3 == 0
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, date(2026, 10, 14)) is False


def test_nightly_export_marks_failed(job_db, monkeypatch: pytest.MonkeyPatch):
    from scripts import nightly_export as ne

    def boom(*_a, **_k):
        raise RuntimeError("export_broke")

    monkeypatch.setattr(ne, "export_telemetry_csv", boom)
    code = ne.run_nightly_export(env={"TARGET_DATE": "2026-10-13", "NIGHTLY_SKIP_PIPELINE": "1"})
    assert code == 1
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is False
    eng = get_job_engine()
    with eng.connect() as conn:
        row = conn.execute(
            text(
                "SELECT status, error_message FROM job_runs WHERE target_date = :d ORDER BY created_at DESC LIMIT 1"
            ),
            {"d": "2026-10-13"},
        ).first()
    assert row is not None
    assert row[0] == "failed"
    assert "export_broke" in (row[1] or "")


def test_csv_path_helper():
    assert csv_path_for(date(2025, 1, 15)).name == "telemetry_2025-01-15.csv"
