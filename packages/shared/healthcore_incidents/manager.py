"""Centralized incident manager enums and lifecycle rules (BRIEFING)."""

from __future__ import annotations

ALLOWED_STATUSES = frozenset({"open", "in_progress", "resolved", "discarded"})
ALLOWED_ORIGINS = frozenset({"customer", "branch", "internal"})
ALLOWED_CATEGORIES = frozenset(
    {
        "clinical_equipment",
        "it_system",
        "billing_error",
        "compliance_breach",
        "patient_experience",
        "staff_issue",
        "facility_issue",
        "referral_issue",
        "other",
    }
)

ALLOWED_BRANCHES = frozenset(
    {
        "central",
        "austin_north",
        "dallas_uptown",
        "houston_med_center",
        "san_antonio_west",
        "miami_brickell",
        "miami_doral",
        "orlando_east",
        "tampa_bay",
        "atlanta_midtown",
        "savannah",
        "london_city",
        "london_west",
        "manchester_central",
    }
)

BRANCH_LABELS: dict[str, str] = {
    "central": "Central — Austin Main Clinic",
    "austin_north": "Austin — North",
    "dallas_uptown": "Dallas Uptown",
    "houston_med_center": "Houston Medical Center",
    "san_antonio_west": "San Antonio West",
    "miami_brickell": "Miami Brickell",
    "miami_doral": "Miami Doral",
    "orlando_east": "Orlando East",
    "tampa_bay": "Tampa Bay",
    "atlanta_midtown": "Atlanta Midtown",
    "savannah": "Savannah",
    "london_city": "London City",
    "london_west": "London West End",
    "manchester_central": "Manchester Central",
}

STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"in_progress", "discarded"}),
    "in_progress": frozenset({"resolved", "discarded"}),
    "resolved": frozenset(),
    "discarded": frozenset(),
}


def can_transition(current: str, new_status: str) -> bool:
    return new_status in STATUS_TRANSITIONS.get(current, frozenset())


def transition_error(current: str, new_status: str) -> str:
    if current in {"resolved", "discarded"}:
        return f"Status '{current}' is final and cannot be changed."
    allowed = sorted(STATUS_TRANSITIONS.get(current, frozenset()))
    if not allowed:
        return f"Status '{current}' cannot transition to '{new_status}'."
    return (
        f"Cannot change status from '{current}' to '{new_status}'. "
        f"Allowed next states: {', '.join(allowed)}."
    )
