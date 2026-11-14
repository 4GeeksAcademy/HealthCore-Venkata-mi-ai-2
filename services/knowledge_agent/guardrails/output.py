"""Validate model/composed answers before they reach the coordinator."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ..memory.phi import phi_scan
from .canned import OUTPUT_PHI_REFUSAL, SYSTEM_LEAK_REFUSAL

FailureType = Literal["structural", "content", "security"]
Action = Literal["allow", "block"]

_SYSTEM_LEAK = (
    re.compile(r"\bSYSTEM_PROMPT\b"),
    re.compile(r"\bhard rules:\s*1\.\s*use only the facts\b", re.IGNORECASE),
    re.compile(r"\byou are the healthcore front-desk knowledge assistant\b", re.IGNORECASE),
    re.compile(r"\bmy (?:system|hidden) (?:prompt|instructions?)\b", re.IGNORECASE),
    re.compile(r"<system>.*</system>", re.IGNORECASE | re.DOTALL),
)

_ACTIVE_BREACH_DETAIL = re.compile(
    r"\b(?:active|open|ongoing)\b.{0,40}\bbreach\b.{0,80}\b"
    r"(?:\d+\s+records?|discovered\s+on|clinic\s+\w+)\b",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class OutputDecision:
    action: Action
    failure_type: FailureType | None
    rule_id: str
    answer: str


def validate_output(
    answer: str,
    *,
    outcome: str | None = None,
    kb_used: bool = False,
) -> OutputDecision:
    text = answer or ""
    scan = phi_scan(text)
    if scan.hit:
        return OutputDecision(
            action="block",
            failure_type="content",
            rule_id="output_phi",
            answer=OUTPUT_PHI_REFUSAL,
        )

    for pattern in _SYSTEM_LEAK:
        if pattern.search(text):
            return OutputDecision(
                action="block",
                failure_type="security",
                rule_id="system_prompt_leak",
                answer=SYSTEM_LEAK_REFUSAL,
            )

    if _ACTIVE_BREACH_DETAIL.search(text):
        return OutputDecision(
            action="block",
            failure_type="content",
            rule_id="active_breach_detail",
            answer=SYSTEM_LEAK_REFUSAL,
        )

    # Structural: KB answers should carry a Source line (tools already append their own).
    if kb_used and outcome == "answered" and "Source:" not in text:
        # Soft fix: allow through but mark structural — still return the answer;
        # the harness logs the structural miss without blocking desk usefulness.
        return OutputDecision(
            action="allow",
            failure_type="structural",
            rule_id="missing_source_line",
            answer=text,
        )

    return OutputDecision(
        action="allow",
        failure_type=None,
        rule_id="ok",
        answer=text,
    )
