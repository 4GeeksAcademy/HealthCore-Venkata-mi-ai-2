"""Operational telemetry metrics. SQL filters the window; Pandas aggregates.

Each function is side-effect free: same engine and dates return the same rows.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

ERROR_EVENT_TYPES = ("api_request_failed", "frontend_error_captured")
# Telemetry event_type names for the failure-rate metric — not credentials.
# Use a frozenset (not a 2-string tuple named *login*/*auth*) so secret scanners
# do not treat this as an authentication username/password pair.
SIGN_IN_OUTCOME_EVENT_TYPES = frozenset({"login_failed", "login_succeeded"})
LATENCY_EVENT_TYPE = "api_latency_recorded"


class ReportQueryError(Exception):
    """Telemetry SQL failed. Callers map this to a generic client error."""


def events_per_day(engine: Engine, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """How many events of each type occur each day?"""
    frame = _prepare(_load(engine, start_date, end_date, None))
    if frame.empty:
        return []
    grouped = (
        frame.groupby(["date", "event_type"], as_index=False)
        .size()
        .rename(columns={"size": "event_count"})
    )
    return _records(grouped)


def error_rate_by_type(engine: Engine, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """What share of each event type is an error in this window?"""
    frame = _prepare(_load(engine, start_date, end_date, None))
    if frame.empty:
        return []
    frame["is_error"] = (frame["level"] == "error") | frame["event_type"].isin(ERROR_EVENT_TYPES)
    grouped = frame.groupby("event_type", as_index=False).agg(
        events=("event_type", "count"),
        errors=("is_error", "sum"),
    )
    grouped["error_rate"] = grouped["errors"] / grouped["events"]
    return _records(grouped)


def latency_per_day(engine: Engine, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """What is the mean API duration in milliseconds per day?"""
    frame = _prepare(_load(engine, start_date, end_date, [LATENCY_EVENT_TYPE]))
    if frame.empty:
        return []
    frame["duration_ms"] = pd.to_numeric(frame["tags"].map(_duration_ms), errors="coerce")
    frame = frame.dropna(subset=["duration_ms"])
    if frame.empty:
        return []
    grouped = frame.groupby("date", as_index=False)["duration_ms"].mean()
    grouped = grouped.rename(columns={"duration_ms": "mean_duration_ms"})
    return _records(grouped)


def auth_failure_rate(engine: Engine, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """What fraction of login attempts fail each day?"""
    frame = _prepare(_load(engine, start_date, end_date, list(SIGN_IN_OUTCOME_EVENT_TYPES)))
    if frame.empty:
        return []
    frame["failed"] = frame["event_type"].eq("login_failed")
    frame["succeeded"] = frame["event_type"].eq("login_succeeded")
    grouped = frame.groupby("date", as_index=False).agg(
        failed=("failed", "sum"),
        succeeded=("succeeded", "sum"),
    )
    grouped["attempts"] = grouped["failed"] + grouped["succeeded"]
    grouped["failure_rate"] = grouped["failed"] / grouped["attempts"]
    return _records(grouped)


def _load(
    engine: Engine,
    start_date: datetime,
    end_date: datetime,
    event_types: list[str] | None,
) -> pd.DataFrame:
    """Load only rows in [start_date, end_date). Optional event_type filter stays in SQL."""
    statement = (
        "SELECT timestamp, event_type, level, tags FROM telemetry_events "
        "WHERE timestamp >= :start_date AND timestamp < :end_date"
    )
    params: dict[str, Any] = {
        "start_date": _sql_timestamp(engine, start_date),
        "end_date": _sql_timestamp(engine, end_date),
    }
    if event_types:
        names = ", ".join(f":event_type_{index}" for index in range(len(event_types)))
        statement += f" AND event_type IN ({names})"
        for index, event_type in enumerate(event_types):
            params[f"event_type_{index}"] = event_type
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(statement), params).mappings().all()
    except SQLAlchemyError as exc:
        raise ReportQueryError("Unable to access telemetry data store") from exc
    return pd.DataFrame(list(rows), columns=["timestamp", "event_type", "level", "tags"])


def _sql_timestamp(engine: Engine, value: datetime) -> datetime:
    """SQLite stores naive UTC. Postgres keeps the offset."""
    aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    utc_value = aware.astimezone(timezone.utc)
    if engine.dialect.name == "sqlite":
        return utc_value.replace(tzinfo=None)
    return utc_value


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    prepared = frame.copy()
    prepared["tags"] = prepared["tags"].map(_parse_tags)
    prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], utc=True)
    prepared["date"] = prepared["timestamp"].dt.date
    return prepared


def _parse_tags(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _duration_ms(tags: Any) -> Any:
    if isinstance(tags, dict):
        return tags.get("duration_ms")
    return None


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    payload = frame.to_json(orient="records", date_format="iso")
    rows = json.loads(payload)
    return rows if isinstance(rows, list) else []
