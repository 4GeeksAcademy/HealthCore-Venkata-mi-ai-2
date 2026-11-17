"""Pull only the paragraphs that match a department. Never return the whole document."""

from __future__ import annotations

from .departments import EXTRACT_KEYWORDS, UNKNOWN_CUES

_EXTRACT_CHAR_CAP = 1800


def paragraphs(text: str) -> list[str]:
    blocks = [block.strip() for block in (text or "").split("\n\n")]
    if len(blocks) <= 1:
        blocks = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return [block for block in blocks if block]


def department_extract(text: str, department_id: str) -> str:
    keys = EXTRACT_KEYWORDS[department_id]
    chosen: list[str] = []
    for block in paragraphs(text):
        lowered = block.lower()
        if any(key in lowered for key in keys):
            chosen.append(block)
    joined = "\n\n".join(chosen).strip()
    if len(joined) > _EXTRACT_CHAR_CAP:
        return joined[:_EXTRACT_CHAR_CAP].rstrip()
    return joined


def unknown_departments(text: str) -> list[str]:
    lowered = (text or "").lower()
    found: list[str] = []
    for department_id, cues in UNKNOWN_CUES.items():
        if any(cue in lowered for cue in cues):
            found.append(department_id)
    return found
