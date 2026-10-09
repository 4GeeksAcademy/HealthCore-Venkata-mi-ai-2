"""Transform accepted supply events into clinic-month KPI rows."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.process.clinic_supply_kpis import (  # noqa: E402
    build_monthly_clinic_supply_rows,
    transform_stats as _transform_stats,
)


def transform_monthly_clinic_kpis(
    events: list[dict[str, Any]],
    month_start: date,
) -> list[dict[str, Any]]:
    return build_monthly_clinic_supply_rows(events, month_start)


def transform_stats(events: list[dict[str, Any]]) -> dict[str, int]:
    return _transform_stats(events)
