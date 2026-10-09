"""UTC month helpers for the clinic supply pipeline."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


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
