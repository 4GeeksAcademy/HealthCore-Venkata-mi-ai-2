"""Proposal departments from the HealthCore RFP briefing. No other ids are workers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Department:
    department_id: str
    name: str
    owner_name: str
    owner_role: str


DEPARTMENTS: dict[str, Department] = {
    "revenue": Department(
        "revenue",
        "Revenue Cycle",
        "Tom Callahan",
        "Revenue Cycle Director",
    ),
    "clinical": Department(
        "clinical",
        "Clinical Operations",
        "Dr. Marcus Reid",
        "Clinical Operations Director",
    ),
    "compliance": Department(
        "compliance",
        "Compliance and Data Governance",
        "Claire Whitfield",
        "Compliance and Data Governance Manager",
    ),
}

DEPARTMENT_IDS: tuple[str, ...] = ("revenue", "clinical", "compliance")

# Mentions that must not spawn a worker. Compliance stays mandatory anyway.
UNKNOWN_DEPARTMENT_CUES: tuple[tuple[str, str], ...] = (
    ("people", "People and Workforce"),
    ("technology", "Technology"),
    ("patient_experience", "Patient Experience and Access"),
    ("executive", "Executive Leadership"),
)

UNKNOWN_CUES: dict[str, tuple[str, ...]] = {
    "people": ("people and workforce", "human resources", "diane foster"),
    "technology": ("technology department", "james osei"),
    "patient_experience": ("patient experience", "priya nair"),
    "executive": ("executive leadership", "dr. okonkwo", "sandra okonkwo"),
}

EXTRACT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "budget",
        "price",
        "pricing",
        "payment",
        "fee",
        "cost",
        "invoice",
        "currency",
        "usd",
        "gbp",
        "proposal",
        "retainer",
    ),
    "clinical": (
        "clinic",
        "physician",
        "nurse",
        "staff",
        "occupational",
        "wellness",
        "on-site",
        "onsite",
        "capacity",
        "appointment",
        "employee",
        "student",
        "referral",
    ),
    "compliance": (
        "hipaa",
        "gdpr",
        "baa",
        "dpa",
        "privacy",
        "business associate",
        "data processing",
        "compliant",
    ),
}
