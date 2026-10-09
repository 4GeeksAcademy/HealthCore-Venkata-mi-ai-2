"""Pure Monthly Clinic Supply KPI transforms (no DB, no Prefect)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

# Keep clinic allowlist in sync with data/pipelines/monthly_clinic_supply/clinics.py
CLINIC_ALLOWLIST: list[dict[str, str]] = [
    {"clinic_id": "us-tx-001", "country": "US", "currency": "USD"},
    {"clinic_id": "us-tx-002", "country": "US", "currency": "USD"},
    {"clinic_id": "us-fl-001", "country": "US", "currency": "USD"},
    {"clinic_id": "us-fl-002", "country": "US", "currency": "USD"},
    {"clinic_id": "us-ga-001", "country": "US", "currency": "USD"},
    {"clinic_id": "us-ga-002", "country": "US", "currency": "USD"},
    {"clinic_id": "uk-lon-001", "country": "UK", "currency": "GBP"},
    {"clinic_id": "uk-lon-002", "country": "UK", "currency": "GBP"},
    {"clinic_id": "uk-man-001", "country": "UK", "currency": "GBP"},
    {"clinic_id": "uk-man-002", "country": "UK", "currency": "GBP"},
]


def supply_cost_per_clinic(events: list[dict[str, Any]]) -> dict[str, float]:
    """Supply Cost per Clinic: sum tags.total_cost on inbound_order_created."""
    costs: dict[str, float] = defaultdict(float)
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "inbound_order_created":
            continue
        clinic_id = event.get("clinic_id")
        if not clinic_id:
            continue
        try:
            costs[str(clinic_id)] += float(event.get("total_cost") or 0)
        except (TypeError, ValueError):
            continue
    return {key: round(value, 2) for key, value in costs.items()}


def supply_consumption_volume(events: list[dict[str, Any]]) -> dict[str, int]:
    """Supply Consumption Volume: count of outbound_order_created per clinic."""
    counts: dict[str, int] = defaultdict(int)
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "outbound_order_created":
            continue
        clinic_id = event.get("clinic_id")
        if clinic_id:
            counts[str(clinic_id)] += 1
    return dict(counts)


def critical_stockout_frequency(events: list[dict[str, Any]]) -> dict[str, int]:
    """Critical Stockout Frequency: count of stock_threshold_triggered per clinic."""
    counts: dict[str, int] = defaultdict(int)
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "stock_threshold_triggered":
            continue
        clinic_id = event.get("clinic_id")
        if clinic_id:
            counts[str(clinic_id)] += 1
    return dict(counts)


def expiry_risk_count(events: list[dict[str, Any]]) -> dict[str, int]:
    """Expiry Risk Count: count of supply_expiry_flagged per clinic."""
    counts: dict[str, int] = defaultdict(int)
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event_type") != "supply_expiry_flagged":
            continue
        clinic_id = event.get("clinic_id")
        if clinic_id:
            counts[str(clinic_id)] += 1
    return dict(counts)


def build_monthly_clinic_supply_rows(
    events: list[dict[str, Any]],
    month_start: date,
) -> list[dict[str, Any]]:
    """Left-join clinic allowlist with the four KPIs for one UTC month."""
    if not isinstance(events, list):
        events = []

    costs = supply_cost_per_clinic(events)
    consumption = supply_consumption_volume(events)
    stockouts = critical_stockout_frequency(events)
    expiry = expiry_risk_count(events)

    rows: list[dict[str, Any]] = []
    for clinic in CLINIC_ALLOWLIST:
        clinic_id = clinic["clinic_id"]
        rows.append(
            {
                "clinic_id": clinic_id,
                "country": clinic["country"],
                "month_start": month_start.isoformat(),
                "total_supply_cost": costs.get(clinic_id, 0.0),
                "supply_consumption_count": consumption.get(clinic_id, 0),
                "critical_stockout_count": stockouts.get(clinic_id, 0),
                "expiry_risk_count": expiry.get(clinic_id, 0),
                "currency": clinic["currency"],
            }
        )
    return rows


def transform_stats(events: list[dict[str, Any]]) -> dict[str, int]:
    if not isinstance(events, list):
        return {
            "distinct_clinic_count": 0,
            "distinct_session_count": 0,
            "distinct_request_id_count": 0,
        }
    clinics = {
        event["clinic_id"]
        for event in events
        if isinstance(event, dict) and event.get("clinic_id")
    }
    sessions = {
        str(event["sessionId"])
        for event in events
        if isinstance(event, dict) and event.get("sessionId")
    }
    requests = {
        str(event["requestId"])
        for event in events
        if isinstance(event, dict) and event.get("requestId")
    }
    return {
        "distinct_clinic_count": len(clinics),
        "distinct_session_count": len(sessions),
        "distinct_request_id_count": len(requests),
    }
