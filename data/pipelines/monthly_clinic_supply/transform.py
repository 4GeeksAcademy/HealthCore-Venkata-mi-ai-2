"""Transform accepted supply events into clinic-month KPI rows."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from .clinics import CLINIC_ALLOWLIST


def transform_monthly_clinic_kpis(
    events: list[dict[str, Any]],
    month_start: date,
) -> list[dict[str, Any]]:
    costs: dict[str, float] = defaultdict(float)
    consumption: dict[str, int] = defaultdict(int)
    stockouts: dict[str, int] = defaultdict(int)
    expiry: dict[str, int] = defaultdict(int)
    active_clinics: set[str] = set()
    sessions: set[str] = set()
    requests: set[str] = set()

    for event in events:
        clinic_id = event["clinic_id"]
        active_clinics.add(clinic_id)
        if event.get("sessionId"):
            sessions.add(str(event["sessionId"]))
        if event.get("requestId"):
            requests.add(str(event["requestId"]))
        event_type = event["event_type"]
        if event_type == "inbound_order_created":
            costs[clinic_id] += float(event.get("total_cost") or 0)
        elif event_type == "outbound_order_created":
            consumption[clinic_id] += 1
        elif event_type == "stock_threshold_triggered":
            stockouts[clinic_id] += 1
        elif event_type == "supply_expiry_flagged":
            expiry[clinic_id] += 1

    rows: list[dict[str, Any]] = []
    for clinic in CLINIC_ALLOWLIST:
        clinic_id = clinic["clinic_id"]
        rows.append(
            {
                "clinic_id": clinic_id,
                "country": clinic["country"],
                "month_start": month_start.isoformat(),
                "total_supply_cost": round(costs.get(clinic_id, 0.0), 2),
                "supply_consumption_count": consumption.get(clinic_id, 0),
                "critical_stockout_count": stockouts.get(clinic_id, 0),
                "expiry_risk_count": expiry.get(clinic_id, 0),
                "currency": clinic["currency"],
            }
        )

    return rows


def transform_stats(events: list[dict[str, Any]]) -> dict[str, int]:
    clinics = {event["clinic_id"] for event in events}
    sessions = {str(event["sessionId"]) for event in events if event.get("sessionId")}
    requests = {str(event["requestId"]) for event in events if event.get("requestId")}
    return {
        "distinct_clinic_count": len(clinics),
        "distinct_session_count": len(sessions),
        "distinct_request_id_count": len(requests),
    }
