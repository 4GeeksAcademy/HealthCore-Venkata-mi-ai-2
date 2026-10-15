"""Export telemetry_events for one UTC day to CSV (backup only — pipeline reads DB)."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .db import get_telemetry_engine, is_sqlite, repo_root

CSV_COLUMNS = (
    "id",
    "timestamp",
    "service",
    "event_type",
    "level",
    "value",
    "message",
    "tags",
)


def csv_path_for(target_date: date, raw_dir: Path | None = None) -> Path:
    base = raw_dir or (repo_root() / "data" / "raw")
    return base / f"telemetry_{target_date.isoformat()}.csv"


def _day_bounds(target_date: date) -> tuple[datetime, datetime]:
    start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def export_telemetry_csv(
    target_date: date,
    *,
    engine: Engine | None = None,
    raw_dir: Path | None = None,
    force: bool = False,
) -> tuple[Path, int, bool]:
    """
    Write `data/raw/telemetry_YYYY-MM-DD.csv` if missing.

    Returns (path, row_count, wrote_new_file).
    """
    path = csv_path_for(target_date, raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and not force:
        return path, 0, False

    eng = engine or get_telemetry_engine()
    start, end = _day_bounds(target_date)
    sqlite = is_sqlite(eng)
    start_p = start.isoformat() if sqlite else start
    end_p = end.isoformat() if sqlite else end

    with eng.connect() as conn:
        # Table may be empty or missing in local dry runs — fail loudly if missing.
        try:
            rows = conn.execute(
                text(
                    """
                    SELECT id, timestamp, service, event_type, level, value, message, tags
                    FROM telemetry_events
                    WHERE timestamp >= :start_ts AND timestamp < :end_ts
                    ORDER BY timestamp ASC
                    """
                ),
                {"start_ts": start_p, "end_ts": end_p},
            ).mappings().all()
        except Exception as exc:
            raise RuntimeError(
                f"Unable to read telemetry_events for {target_date.isoformat()}: {exc}"
            ) from exc

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({col: _cell(row.get(col)) for col in CSV_COLUMNS})

    return path, len(rows), True
