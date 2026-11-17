"""Redact patient identifiers before any model call, log line, or ticket field.

Program words such as "diabetes" inside a scope of work are not PHI.
A labeled patient name, record number, or diagnosis is.
"""

from __future__ import annotations

import re

_REPLACEMENT = "[REDACTED]"

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:MRN|NHS(?:\s+number)?|member\s+id)\s*[:#]?\s*[A-Z0-9-]{4,}\b", re.I),
    re.compile(
        r"\b(?:patient|pt)\s+name\s*[:\-]\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
        re.I,
    ),
    re.compile(
        r"\bpatient\s*[:\-]\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
        re.I,
    ),
    re.compile(r"\bdiagnos(?:is|ed)\s*[:\-]\s*[^\n.]{3,120}", re.I),
    re.compile(
        r"\b(?:DOB|date of birth)\s*[:\-]\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        re.I,
    ),
)


def redact(text: str) -> tuple[str, bool]:
    """Return text with PHI spans replaced, and whether any span matched."""
    if not text:
        return "", False
    found = False
    cleaned = text
    for pattern in _PATTERNS:
        cleaned, count = pattern.subn(_REPLACEMENT, cleaned)
        if count:
            found = True
    return cleaned, found


def contains_phi(text: str) -> bool:
    return redact(text)[1]
