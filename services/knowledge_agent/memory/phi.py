"""Deterministic PHI gate for agent memory.

One rule set covers both regimes HealthCore operates under:

- HIPAA identifiers the briefing names: patient name, medical record number,
  date of birth, Social Security number, insurance or member number, and
  clinical content from a visit.
- UK GDPR special-category health data (Article 9) and direct identifiers
  that can re-identify a person, including an NHS number and the same
  clinical content.

A hit means the text must not be stored, logged, or sent to a model.
The scan result names the rule ids only. It does not keep the matched span.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# "patient" itself may be capitalised at the start of a sentence. The name
# after it stays case-sensitive so "a new patient bring" is not a name.
_PATIENT_NAME = re.compile(r"\b(?i:patients?)\s+([A-Z][a-z]{2,})\b")
_NAME_ALLOW = frozenset(
    {
        "Experience",
        "Access",
        "Coordinator",
        "Coordinators",
        "Should",
        "Bring",
        "Please",
        "Information",
    }
)

# Age + named person + clinic (or age + diagnosis + clinic) can re-identify.
_QUASI_ID = re.compile(
    r"\b(?:patient|i have)\b.{0,80}\b(?:\d{1,3})\b.{0,80}\b(?:diagnos|clinic|austin|manchester|london)\b",
    re.IGNORECASE | re.DOTALL,
)
_NAMED_AGE_CLINIC = re.compile(
    r"\b([A-Z][a-z]{2,})\b(?:\s*,\s*|\s+)\d{1,3}\b.{0,60}\b(?:clinic|diagnos)",
    re.DOTALL,
)

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("mrn", re.compile(r"\b(?:mrn|medical record(?: number)?)\b", re.IGNORECASE)),
    ("dob", re.compile(r"\b(?:d\.?o\.?b\.?|date of birth)\b", re.IGNORECASE)),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "insurance_number",
        re.compile(r"\b(?:insurance|member|subscriber)\s*(?:id|number|#)\b", re.IGNORECASE),
    ),
    ("nhs_number", re.compile(r"\bnhs\s*(?:number|no\.?)?\s*\d", re.IGNORECASE)),
    ("diagnosis", re.compile(r"\bdiagnos(?:is|es)\b", re.IGNORECASE)),
    (
        "clinical_content",
        re.compile(
            r"\b(?:lab results?|clinical notes?|progress notes?|prescriptions?|discharge summary)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class PhiScan:
    hit: bool
    rules: tuple[str, ...]


def phi_scan(text: str) -> PhiScan:
    """Return which forbidden classes appear. The matched text is discarded."""
    found: list[str] = []
    body = text or ""
    name = _PATIENT_NAME.search(body)
    if name and name.group(1) not in _NAME_ALLOW:
        found.append("patient_name")
    for rule_id, pattern in _RULES:
        if pattern.search(body):
            found.append(rule_id)
    if _QUASI_ID.search(body) or _NAMED_AGE_CLINIC.search(body):
        found.append("quasi_identifier")
    return PhiScan(hit=bool(found), rules=tuple(found))


def redact(text: str, scan: PhiScan) -> str:
    """Audit stand-in. Hash and rule ids only — never the identifier itself."""
    digest = hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:12]
    rules = ",".join(scan.rules) if scan.rules else "none"
    return f"[redacted sha256={digest} chars={len(text or '')} rules={rules}]"
