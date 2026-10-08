"""Clinic allowlist for the Monthly Clinic Supply Performance Report."""

from __future__ import annotations

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

CLINIC_BY_ID = {row["clinic_id"]: row for row in CLINIC_ALLOWLIST}

SOURCE_EVENT_TYPES = (
    "inbound_order_created",
    "outbound_order_created",
    "stock_threshold_triggered",
    "supply_expiry_flagged",
)

DEPARTMENT_ALLOWLIST = frozenset(
    {
        "general_consultation",
        "chronic_care",
        "primary_care",
        "specialty_care",
        "chronic_disease_management",
    }
)

PRODUCT_CATEGORIES = frozenset({"medication", "ppe", "consumable", "equipment"})

FLOW_NAME = "monthly_clinic_supply_performance"
