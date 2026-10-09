"""Unit tests for Monthly Clinic Supply Performance transforms (Part 3)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PIPELINES = _REPO_ROOT / "data" / "pipelines"
for location in (str(_REPO_ROOT), str(_PIPELINES)):
    if location not in sys.path:
        sys.path.insert(0, location)

from data.process.clinic_supply_kpis import (  # noqa: E402
    build_monthly_clinic_supply_rows,
    critical_stockout_frequency,
    expiry_risk_count,
    supply_consumption_volume,
    supply_cost_per_clinic,
)
from monthly_clinic_supply.extract import accept_event  # noqa: E402


def _event(
    event_type: str,
    clinic_id: str,
    *,
    total_cost: float | None = None,
    session_id: str = "sess-1",
    request_id: str = "req-1",
) -> dict:
    row: dict = {
        "event_type": event_type,
        "clinic_id": clinic_id,
        "sessionId": session_id,
        "requestId": request_id,
    }
    if total_cost is not None:
        row["total_cost"] = total_cost
    return row


def test_supply_cost_per_clinic_sums_inbound_total_cost():
    """Supply Cost per Clinic = sum of inbound_order_created.total_cost."""
    events = [
        _event("inbound_order_created", "us-tx-001", total_cost=100.0),
        _event("inbound_order_created", "us-tx-001", total_cost=50.5),
        _event("outbound_order_created", "us-tx-001"),
        _event("inbound_order_created", "uk-lon-001", total_cost=20.0),
    ]
    costs = supply_cost_per_clinic(events)
    assert costs["us-tx-001"] == 150.5
    assert costs["uk-lon-001"] == 20.0


def test_supply_consumption_volume_counts_outbound_orders():
    """Supply Consumption Volume = count of outbound_order_created."""
    events = [
        _event("outbound_order_created", "us-fl-001"),
        _event("outbound_order_created", "us-fl-001"),
        _event("outbound_order_created", "us-fl-002"),
        _event("inbound_order_created", "us-fl-001", total_cost=10.0),
    ]
    volumes = supply_consumption_volume(events)
    assert volumes["us-fl-001"] == 2
    assert volumes["us-fl-002"] == 1


def test_critical_stockout_frequency_counts_threshold_events():
    """Critical Stockout Frequency = count of stock_threshold_triggered."""
    events = [
        _event("stock_threshold_triggered", "us-ga-001"),
        _event("stock_threshold_triggered", "us-ga-001"),
        _event("stock_threshold_triggered", "us-ga-001"),
        _event("supply_expiry_flagged", "us-ga-001"),
    ]
    assert critical_stockout_frequency(events)["us-ga-001"] == 3


def test_expiry_risk_count_counts_expiry_flags():
    """Expiry Risk Count = count of supply_expiry_flagged."""
    events = [
        _event("supply_expiry_flagged", "uk-man-001"),
        _event("supply_expiry_flagged", "uk-man-001"),
        _event("stock_threshold_triggered", "uk-man-001"),
    ]
    assert expiry_risk_count(events)["uk-man-001"] == 2


def test_hand_calculated_kpi_row_matches_context_definitions():
    """
    Hand-calculated pack for us-tx-001 in 2026-09:
    - Supply Cost: 100 + 25.50 = 125.50
    - Consumption: 2 outbound
    - Stockouts: 1 threshold
    - Expiry: 0
    Quiet clinics still appear with zeros (allowlist left-join).
    """
    events = [
        _event("inbound_order_created", "us-tx-001", total_cost=100.0),
        _event("inbound_order_created", "us-tx-001", total_cost=25.50),
        _event("outbound_order_created", "us-tx-001"),
        _event("outbound_order_created", "us-tx-001"),
        _event("stock_threshold_triggered", "us-tx-001"),
    ]
    rows = build_monthly_clinic_supply_rows(events, date(2026, 9, 1))
    by_clinic = {row["clinic_id"]: row for row in rows}
    assert len(rows) == 10
    target = by_clinic["us-tx-001"]
    assert target["month_start"] == "2026-09-01"
    assert target["total_supply_cost"] == 125.50
    assert target["supply_consumption_count"] == 2
    assert target["critical_stockout_count"] == 1
    assert target["expiry_risk_count"] == 0
    assert target["currency"] == "USD"
    quiet = by_clinic["uk-man-002"]
    assert quiet["total_supply_cost"] == 0.0
    assert quiet["supply_consumption_count"] == 0


def test_accept_event_rejects_malformed_inbound_without_total_cost():
    """Defensive: inbound without a numeric total_cost is rejected."""
    tags = {
        "eventId": "evt-bad-1",
        "clinic_id": "us-tx-001",
        "country": "US",
        "product_category": "medication",
        "product_id": "med-1",
        "quantity": 2,
        "total_cost": None,
    }
    assert accept_event("inbound_order_created", tags) is False


def test_supply_cost_per_clinic_skips_invalid_total_cost_type():
    """Defensive: non-numeric total_cost does not break the transform."""
    events = [
        {
            "event_type": "inbound_order_created",
            "clinic_id": "us-tx-001",
            "total_cost": "not-a-number",
        },
        _event("inbound_order_created", "us-tx-001", total_cost=40.0),
    ]
    costs = supply_cost_per_clinic(events)
    assert costs["us-tx-001"] == 40.0


def test_build_rows_tolerates_non_list_events():
    """Defensive: malformed events container yields zero rows for all clinics."""
    rows = build_monthly_clinic_supply_rows(None, date(2026, 9, 1))  # type: ignore[arg-type]
    assert len(rows) == 10
    assert all(row["total_supply_cost"] == 0.0 for row in rows)
