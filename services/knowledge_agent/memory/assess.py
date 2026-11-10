"""Explicit memorable-fact criterion. Most turns produce no proposal.

A proposal is returned only for a durable operational fact of a kind the
HealthCore briefing allows. A policy question, a ticket lookup, a closing,
and a one-off metric query do not match, so they are not proposed.

The model is not asked to invent the fact. The user's own sentence is the
fact, after the PHI gate and the published-policy guard. That keeps a
paraphrase from introducing a patient detail the user did not need stored.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .phi import PhiScan, phi_scan

Kind = Literal["clinic_protocol", "incident_pattern", "staff_preference", "admin_exception"]

_CLINICS: tuple[tuple[str, str], ...] = (
    ("manchester", "Manchester"),
    ("austin", "Austin"),
    ("london", "London"),
    ("houston", "Houston"),
    ("dallas", "Dallas"),
    ("miami", "Miami"),
    ("atlanta", "Atlanta"),
    ("orlando", "Orlando"),
    ("tampa", "Tampa"),
    ("san antonio", "San Antonio"),
)
_STAFF: tuple[tuple[str, str], ...] = (
    ("diane foster", "Diane Foster"),
    ("tom callahan", "Tom Callahan"),
    ("marcus reid", "Marcus Reid"),
    ("priya nair", "Priya Nair"),
    ("claire whitfield", "Claire Whitfield"),
    ("james osei", "James Osei"),
    ("sandra okonkwo", "Sandra Okonkwo"),
)

_PROTOCOL = re.compile(
    r"\b(?:now goes? through|from now on|that changed|changed last|local protocol|front[- ]desk)\b",
    re.IGNORECASE,
)
_PATTERN = re.compile(
    r"\b(?:road closure|overnight batch|fails on mondays?|not a real problem)\b",
    re.IGNORECASE,
)
_PREFERENCE = re.compile(
    r"\b(?:broken down by|asked for|prefers|wants the|needs \w+ by role)\b",
    re.IGNORECASE,
)
_COUNTRY = re.compile(r"\b(?:united kingdom|united states|\buk\b|\bus\b)\b", re.IGNORECASE)
_EXCEPTION = re.compile(r"\b(?:exception|differs|instead of the)\b", re.IGNORECASE)
_CLOSING = re.compile(
    r"^\s*(?:thanks|thank you|that settles|that's all|that is all|goodbye|cheers)\b",
    re.IGNORECASE,
)
_REMEMBER = re.compile(
    r"\b(?:remember|note that|note that down|store this|save this|write that down)\b",
    re.IGNORECASE,
)

_WHY = {
    "clinic_protocol": "Recurring front-desk protocol for this clinic.",
    "incident_pattern": "Operational incident pattern with no patient detail.",
    "staff_preference": "How this staff member wants operational information presented.",
    "admin_exception": "Administrative exception that differs by country.",
}


class MemoryProposal(BaseModel):
    """The extra field on a turn. Null when there is nothing to remember."""

    model_config = ConfigDict(extra="forbid")

    kind: Kind
    scope: str = Field(min_length=2, max_length=80)
    fact: str = Field(min_length=12, max_length=500)
    why: str = Field(min_length=8, max_length=200)


class MemoryAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_proposal: MemoryProposal | None = None
    blocked: Literal["none", "phi", "policy"] = "none"
    phi_rules: tuple[str, ...] = ()


def clean_fact(text: str) -> str:
    return " ".join((text or "").split())[:500]


def policy_conflict(text: str) -> bool:
    """A desk note must not overwrite published coverage or the no-show fee rule."""
    lowered = (text or "").lower()
    fee = any(word in lowered for word in ("fee", "charge", "charged", "pay", "paying"))
    no_show = "no-show" in lowered or "no show" in lowered or "noshow" in lowered
    if no_show and fee and ("medicare" in lowered or "medicaid" in lowered):
        return True
    if "humana" in lowered and any(
        word in lowered for word in ("accepted", "accept", "covered", "in-network", "in network")
    ):
        return True
    return False


def _canon(text: str, pairs: tuple[tuple[str, str], ...]) -> str | None:
    lowered = text.lower()
    for needle, label in pairs:
        if needle in lowered:
            return label
    return None


def _country(text: str) -> str | None:
    match = _COUNTRY.search(text or "")
    if not match:
        return None
    token = match.group(0).lower()
    if token in {"uk", "united kingdom"}:
        return "United Kingdom"
    return "United States"


def match_proposal(text: str) -> MemoryProposal | None:
    """Return a proposal only when the briefing's memorable kinds all match."""
    body = clean_fact(text)
    if not body or _CLOSING.match(body):
        return None
    clinic = _canon(body, _CLINICS)
    staff = _canon(body, _STAFF)
    if _PATTERN.search(body):
        return MemoryProposal(
            kind="incident_pattern",
            scope=clinic or "network",
            fact=body,
            why=_WHY["incident_pattern"],
        )
    if staff and _PREFERENCE.search(body):
        return MemoryProposal(
            kind="staff_preference",
            scope=staff,
            fact=body,
            why=_WHY["staff_preference"],
        )
    if clinic and _PROTOCOL.search(body):
        return MemoryProposal(
            kind="clinic_protocol",
            scope=clinic,
            fact=body,
            why=_WHY["clinic_protocol"],
        )
    country = _country(body)
    if country and _EXCEPTION.search(body) and _PROTOCOL.search(body):
        return MemoryProposal(
            kind="admin_exception",
            scope=country,
            fact=body,
            why=_WHY["admin_exception"],
        )
    return None


def is_remember_request(text: str) -> bool:
    return _REMEMBER.search(text or "") is not None


def assess_message(text: str, *, already_stored: bool) -> MemoryAssessment:
    """PHI first, then published-policy poison, then the memorable-kind criterion."""
    scan: PhiScan = phi_scan(text)
    if scan.hit:
        return MemoryAssessment(blocked="phi", phi_rules=scan.rules)
    proposal = match_proposal(text)
    if proposal is not None and policy_conflict(proposal.fact):
        return MemoryAssessment(blocked="policy")
    if proposal is None and is_remember_request(text) and policy_conflict(text):
        return MemoryAssessment(blocked="policy")
    if proposal is None or already_stored:
        return MemoryAssessment()
    return MemoryAssessment(memory_proposal=proposal)
