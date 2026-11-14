"""Deterministic input classifier for scope, personal use, and jailbreaks.

No live LLM. Patterns are fixtures for CI; failure types follow the MS8 harness
taxonomy: security (jailbreak), content (personal / identifiable), structural
is reserved for blank/length (handled by receive_question).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ..memory.phi import phi_scan
from .canned import (
    ACTIVE_BREACH_REFUSAL,
    IDENTIFIABLE_REFUSAL,
    JAILBREAK_REFUSAL,
    PERSONAL_TASK_REFUSAL,
)

InputClass = Literal[
    "in_domain",
    "casual",
    "personal_task",
    "jailbreak",
    "identifiable_patient",
    "active_breach_probe",
]
FailureType = Literal["structural", "content", "security"]
Action = Literal["allow", "allow_redirect", "block"]

_JAILBREAK = (
    re.compile(
        r"\bignore\b.{0,40}\b(?:previous\s+)?(?:instructions?|rules?|prompt)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\bact\s+as\s+(?:if\s+)?(?:you\s+had\s+)?(?:an?\s+)?(?:assistant\s+with\s+)?no\s+"
        r"(?:compliance\s+)?(?:rules?|restrictions?|guardrails?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:forget|disregard)\b.{0,40}\b(?:you\s+work\s+for|healthcore|compliance|"
        r"system\s+prompt|instructions?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:you\s+are\s+now|pretend\s+you\s+are|roleplay\s+as)\b.{0,60}\b"
        r"(?:no\s+rules|unrestricted|dan|jailbreak)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:override|bypass)\b.{0,30}\b(?:system|safety|guardrail|compliance)\b",
        re.IGNORECASE,
    ),
)

_PERSONAL = (
    re.compile(
        r"\b(?:write|draft|help\s+me\s+(?:write|draft|with))\b.{0,80}\b"
        r"(?:personal\s+email|love\s+poem|essay|homework|university|salary\s+raise|"
        r"cover\s+letter|resume|cv)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:write|generate|give)\s+(?:me\s+)?(?:some\s+)?(?:python|javascript|code)\b"
        r".{0,40}\b(?:for\s+(?:my|another)|project|homework)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:act\s+as\s+(?:my\s+)?therapist|relationship\s+advice|dating\s+advice)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bhelp\s+me\s+draft\s+a\s+personal\s+email\b",
        re.IGNORECASE,
    ),
)

_CASUAL = (
    re.compile(r"\bwhat\s+time\s+is\s+it\b", re.IGNORECASE),
    re.compile(r"\b(?:tokyo|london|new\s+york|paris)\b.{0,20}\btime\b", re.IGNORECASE),
    re.compile(r"\b(?:how(?:'s| is) (?:your|the) (?:day|shift)|good\s+(?:morning|afternoon))\b", re.IGNORECASE),
    re.compile(r"\b(?:tell\s+me\s+a\s+joke|who\s+won\s+the\s+(?:game|match)|capital\s+of)\b", re.IGNORECASE),
    re.compile(r"\b(?:weather|sports\s+score)\b", re.IGNORECASE),
)

_DOMAIN = (
    re.compile(
        r"\b(?:hipaa|gdpr|baa|dpa|breach\s+notification|compliance|insurance|"
        r"appointment|cancellation|referral|new\s+patient|inventory|ticket|incident|"
        r"healthcore|no-?show|medicare|medicaid|policy|procedure|clinic)\b",
        re.IGNORECASE,
    ),
)

_ACTIVE_BREACH = (
    re.compile(
        r"\b(?:active|open|ongoing|under[- ]investigation)\b.{0,40}\b(?:breach|incident)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:how\s+many\s+records|which\s+clinic).{0,40}\b(?:breach|compromised)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\bwhen\s+was\s+(?:the\s+)?(?:breach|incident)\s+(?:discovered|detected)\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class InputDecision:
    classification: InputClass
    action: Action
    failure_type: FailureType | None
    rule_id: str
    answer: str | None
    redirect_required: bool


def classify_input(question: str) -> InputDecision:
    text = (question or "").strip()
    if not text:
        return InputDecision(
            classification="in_domain",
            action="allow",
            failure_type=None,
            rule_id="empty_deferred",
            answer=None,
            redirect_required=False,
        )

    for pattern in _JAILBREAK:
        if pattern.search(text):
            return InputDecision(
                classification="jailbreak",
                action="block",
                failure_type="security",
                rule_id="jailbreak_instruction_change",
                answer=JAILBREAK_REFUSAL,
                redirect_required=False,
            )

    scan = phi_scan(text)
    if scan.hit and (
        "patient_name" in scan.rules
        or "quasi_identifier" in scan.rules
        or "diagnosis" in scan.rules
        or "mrn" in scan.rules
        or "dob" in scan.rules
    ):
        # Desk questions that only mention Medicare diagnosis-adjacent words without
        # a named patient stay in-domain when no name/quasi pattern fired alone —
        # but "diagnosed with" plus a person is already covered by phi_scan.
        if any(
            r in scan.rules
            for r in ("patient_name", "quasi_identifier", "mrn", "dob", "ssn", "nhs_number")
        ) or ("diagnosis" in scan.rules and re.search(r"\bpatient\b|\b[A-Z][a-z]{2,}\b", text)):
            return InputDecision(
                classification="identifiable_patient",
                action="block",
                failure_type="content",
                rule_id="identifiable_patient",
                answer=IDENTIFIABLE_REFUSAL,
                redirect_required=False,
            )

    for pattern in _ACTIVE_BREACH:
        if pattern.search(text):
            return InputDecision(
                classification="active_breach_probe",
                action="block",
                failure_type="content",
                rule_id="active_breach_probe",
                answer=ACTIVE_BREACH_REFUSAL,
                redirect_required=False,
            )

    for pattern in _PERSONAL:
        if pattern.search(text):
            return InputDecision(
                classification="personal_task",
                action="block",
                failure_type="content",
                rule_id="personal_chatbot_use",
                answer=PERSONAL_TASK_REFUSAL,
                redirect_required=False,
            )

    if any(p.search(text) for p in _CASUAL) and not any(p.search(text) for p in _DOMAIN):
        return InputDecision(
            classification="casual",
            action="allow_redirect",
            failure_type="content",
            rule_id="casual_redirect",
            answer=None,
            redirect_required=True,
        )

    return InputDecision(
        classification="in_domain",
        action="allow",
        failure_type=None,
        rule_id="in_domain",
        answer=None,
        redirect_required=False,
    )
