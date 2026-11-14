"""CSV → centralized incident manager transforms (HealthCore BRIEFING)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .analyzer import validate_csv_row
from .manager import ALLOWED_BRANCHES

STATUS_MAP = {
    "OPEN": "open",
    "CLOSED": "resolved",
    "DISCARDED": "discarded",
}

CATEGORY_MAP = {
    "APPOINTMENT": "patient_experience",
    "BILLING": "billing_error",
    "CLINICAL_CARE": "patient_experience",
    "ACCESSIBILITY": "patient_experience",
    "ADMINISTRATIVE": "other",
}

BRANCH_MAP = {
    "US-TX-01": "central",
    "US-TX-02": "austin_north",
    "US-TX-03": "houston_med_center",
    "US-FL-01": "miami_brickell",
    "US-FL-02": "orlando_east",
    "US-FL-03": "tampa_bay",
    "US-GA-01": "atlanta_midtown",
    "US-GA-02": "atlanta_midtown",
    "US-GA-03": "savannah",
    "UK-LON-01": "london_city",
    "UK-LON-02": "london_west",
    "UK-MAN-01": "manchester_central",
}


def csv_row_to_incident(row: dict[str, str]) -> dict[str, Any] | None:
    """Transform a validated CSV row into a manager incident payload.

    Returns None when the row cannot be mapped (should be rare after validation).
    Never copies patient_id.
    """
    if validate_csv_row(row):
        return None

    description = (row.get("description") or "").strip()
    title = description[:120].strip()
    if not title:
        return None

    status = STATUS_MAP.get((row.get("status") or "").strip())
    category = CATEGORY_MAP.get((row.get("category") or "").strip())
    if status is None or category is None:
        return None

    clinic_id = (row.get("clinic_id") or "").strip()
    branch = BRANCH_MAP.get(clinic_id, "central")
    if branch not in ALLOWED_BRANCHES:
        branch = "central"

    date_raw = (row.get("date") or "").strip()
    try:
        created = datetime.strptime(date_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    created_at = created.replace(microsecond=0).isoformat()

    source_key = (row.get("incident_id") or "").strip()
    if not source_key:
        source_key = f"{title}|{created_at}"

    return {
        "source_key": source_key,
        "title": title,
        "description": description,
        "category": category,
        "status": status,
        "origin": "customer",
        "branch": branch,
        "created_at": created_at,
        "updated_at": created_at,
    }


def transform_valid_rows(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Return (transformed incidents, rejected rows with reason codes — no PHI)."""
    transformed: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for row in rows:
        problems = validate_csv_row(row)
        if problems:
            rejected.append(
                {
                    "incident_id": (row.get("incident_id") or "").strip() or "(missing)",
                    "reason": ",".join(problems),
                }
            )
            continue
        incident = csv_row_to_incident(row)
        if incident is None:
            rejected.append(
                {
                    "incident_id": (row.get("incident_id") or "").strip() or "(missing)",
                    "reason": "transform_failed",
                }
            )
            continue
        transformed.append(incident)
    return transformed, rejected
