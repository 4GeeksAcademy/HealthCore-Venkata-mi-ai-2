"""Structured decision for the one pending proposal.

The label is an enum with a confidence score. Approval requires the message
to start with a decision word as its own word. A substring test is wrong
here: ``"yes" in "yesterday"`` is true, and that message is not an approval.
Anything below 0.75, including a topic change, is ``ambiguous`` and the
caller rejects the proposal.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CONFIDENCE_THRESHOLD = 0.75

_EDIT = re.compile(
    r"^\s*(?:(?:yes|no|yeah|nope)[\s,.]*)?(?:please\s+)?"
    r"(?:remember (?:it|this) as|change (?:it|that) to|correct it to)\s*:?\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)
_REJECT = re.compile(r"^\s*(?:no|nope|nah|don'?t|do not)\b", re.IGNORECASE)
_APPROVE = re.compile(
    r"^\s*(?:yes|yeah|yep|yup|ok|okay|sure|approved?|go ahead|please remember that|"
    r"remember that|store it|keep that)\b",
    re.IGNORECASE,
)
_PREFIX = re.compile(
    r"^(?:(?:"
    r"please remember that|remember that|remember it|go ahead|store it|keep that|"
    r"do not remember|don't remember|do not|don't|"
    r"yes|yeah|yep|yup|ok|okay|sure|no|nope|nah|please|approved?|and|but"
    r")\b[\s,.]*)+",
    re.IGNORECASE,
)


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Literal["approve", "reject", "edit", "ambiguous"]
    confidence: float = Field(ge=0, le=1)
    edited_fact: str | None = None
    follow_up: str | None = None


def _follow_up(message: str) -> str | None:
    rest = _PREFIX.sub("", message).strip(" ,.;")
    if len(rest) < 8:
        return None
    return " ".join(rest.split())


def classify_decision(pending_text: str, message: str) -> Decision:
    """Classify ``message`` as the user's answer to ``pending_text``."""
    if not (pending_text or "").strip() or not (message or "").strip():
        return Decision(label="ambiguous", confidence=0.0)

    edited = _EDIT.match(message.strip())
    if edited:
        fact = " ".join(edited.group(1).split())
        if len(fact) >= 12:
            return Decision(label="edit", confidence=0.92, edited_fact=fact[:500])
        return Decision(label="ambiguous", confidence=0.4)

    if _REJECT.match(message):
        return Decision(label="reject", confidence=0.92, follow_up=_follow_up(message))
    if _APPROVE.match(message):
        return Decision(label="approve", confidence=0.92, follow_up=_follow_up(message))
    return Decision(label="ambiguous", confidence=0.35)
