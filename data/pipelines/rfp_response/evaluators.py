"""Readability, relevance, and briefing compliance for one proposal section.

The three checkers run together. They return their slices. They do not write
the ticket. A second pool runs one section per department at the same time.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from data.pipelines.rfp_intake.metrics import measure
from data.pipelines.rfp_intake.phi import contains_phi, redact

_BAA = re.compile(r"business associate agreement|\bbaa\b", re.I)
_DPA = re.compile(r"data processing agreement|\bdpa\b", re.I)
_UK_GDPR = re.compile(r"uk gdpr", re.I)
_REFUSAL = re.compile(r"\b(?:no|not|without|never|omit|refuses|refuse)\b", re.I)
_HEADCOUNT = re.compile(
    r"(?:covered\s+population|population|headcount)\D{0,16}(\d[\d,]*)"
    r"|(\d[\d,]*)\s+(?:employees|students|staff|clinicians|nurses|physicians|lives)\b",
    re.I,
)
_STOP = frozenset(
    "a an the and or of to for in on with this that from by be is are was will must were been".split()
)

MIN_WORDS = 80
MIN_EASE = 30
MAX_FOG = 22


def _clause_ok(text: str, phrase: re.Pattern[str]) -> bool:
    present = False
    refused = False
    for sentence in re.split(r"[.!?\n]", text or ""):
        if not phrase.search(sentence):
            continue
        if _REFUSAL.search(sentence):
            refused = True
        else:
            present = True
    return present and not refused


def _unique(ids: list[str]) -> list[str]:
    seen: list[str] = []
    for rule_id in ids:
        if rule_id not in seen:
            seen.append(rule_id)
    return seen


def check_readability(text: str) -> dict[str, Any]:
    measured = measure(text or "")
    words = int(measured.get("word_count") or 0)
    ease = measured.get("flesch_reading_ease")
    fog = measured.get("gunning_fog")
    reasons: list[str] = []
    if words < MIN_WORDS:
        reasons.append(
            f"This section has {words} words. Write at least {MIN_WORDS} words in short sentences."
        )
    if ease is not None and float(ease) < MIN_EASE:
        reasons.append(
            f"Flesch reading ease is {ease}, below {MIN_EASE}. Use shorter sentences and simpler words."
        )
    if fog is not None and float(fog) > MAX_FOG:
        reasons.append(f"Gunning fog is {fog}, above {MAX_FOG}. Split long sentences.")
    if reasons:
        details = " ".join(reasons)
    elif ease is not None:
        details = f"{words} words. Flesch reading ease {ease}. Gunning fog {fog}."
    else:
        details = f"{words} words. Grade indexes were not computed."
    return {
        "pass": not reasons,
        "score": ease,
        "details": details,
        "feedback": details if reasons else "",
    }


def _covered(aspect: str, draft: str) -> bool:
    haystack = (draft or "").lower()
    if aspect.lower() in haystack:
        return True
    words = [
        word
        for word in re.findall(r"[a-z0-9']+", aspect.lower())
        if len(word) > 4 and word not in _STOP
    ]
    if not words:
        return False
    hits = sum(1 for word in words if word in haystack)
    return hits * 2 >= len(words)


def check_relevance(
    text: str,
    *,
    department_id: str,
    metadata: dict[str, Any],
    key_aspects: list[str],
) -> dict[str, Any]:
    missing: list[str] = []
    for aspect in key_aspects:
        cleaned = str(aspect).strip()
        if cleaned and not _covered(cleaned, text or ""):
            missing.append(cleaned)
    client = str(metadata.get("client_name") or "").strip()
    if client and client.lower() not in (text or "").lower():
        missing.append(f"the client {client}")
    country = str(metadata.get("client_country") or "")
    required = {"US": "USD", "UK": "GBP"}.get(country, "")
    if department_id == "revenue" and required and required not in (text or ""):
        missing.append(f"pricing currency {required}")
    if department_id == "clinical" and not re.search(r"clinic|capacity|staff", text or "", re.I):
        missing.append("clinic capacity for this program")
    if department_id == "compliance" and country == "US" and not _clause_ok(text or "", _BAA):
        missing.append("a Business Associate Agreement clause")
    if department_id == "compliance" and country == "UK" and not (
        _clause_ok(text or "", _DPA) and _clause_ok(text or "", _UK_GDPR)
    ):
        missing.append("a Data Processing Agreement clause that references UK GDPR")
    feedback = ""
    if missing:
        feedback = "The draft does not cover these RFP points: " + "; ".join(missing) + "."
    return {"pass": not missing, "missing_aspects": missing, "feedback": feedback}


def _population_violations(text: str, metadata: dict[str, Any]) -> list[dict[str, str]]:
    expected = metadata.get("covered_population")
    found: list[int] = []
    for match in _HEADCOUNT.finditer(text or ""):
        raw = match.group(1) or match.group(2) or ""
        found.append(int(raw.replace(",", "")))
    if expected is None and found:
        return [
            {
                "rule_id": "HC-POP-01",
                "detail": "The request has no covered population. Remove the headcount. Do not invent one.",
            }
        ]
    if isinstance(expected, int) and any(number != expected for number in found):
        return [
            {
                "rule_id": "HC-POP-01",
                "detail": (
                    f"Covered population on the ticket is {expected}. Remove any other headcount."
                ),
            }
        ]
    return []


def _currency_violations(
    text: str,
    department_id: str,
    metadata: dict[str, Any],
) -> list[dict[str, str]]:
    country = str(metadata.get("client_country") or "")
    required = {"US": "USD", "UK": "GBP"}.get(country, "")
    if not required:
        return []
    other = "GBP" if required == "USD" else "USD"
    violations: list[dict[str, str]] = []
    if other in (text or ""):
        violations.append(
            {
                "rule_id": "HC-CUR-01",
                "detail": f"The client country is {country}. Quote {required} only. Remove {other}.",
            }
        )
    if department_id == "revenue" and required not in (text or ""):
        violations.append(
            {
                "rule_id": "HC-CUR-01",
                "detail": f"The revenue section must quote {required} for this {country} client.",
            }
        )
    return violations


def check_compliance(
    text: str,
    *,
    department_id: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    country = str(metadata.get("client_country") or "")
    checked = ["HC-PHI-01", "HC-POP-01"]
    if country in {"US", "UK"}:
        checked.append("HC-CUR-01")
    if department_id == "compliance" and country == "US":
        checked.append("HC-BAA-01")
    if department_id == "compliance" and country == "UK":
        checked.append("HC-DPA-01")
    violations: list[dict[str, str]] = []
    phi = contains_phi(text or "")
    if phi:
        violations.append(
            {
                "rule_id": "HC-PHI-01",
                "detail": "Remove the patient name, diagnosis, or other patient identifier.",
            }
        )
    violations.extend(_population_violations(text or "", metadata))
    violations.extend(_currency_violations(text or "", department_id, metadata))
    if department_id == "compliance" and country == "US" and not _clause_ok(text or "", _BAA):
        violations.append(
            {
                "rule_id": "HC-BAA-01",
                "detail": (
                    "Add a Business Associate Agreement (BAA) clause for this US client. "
                    "Do not refuse the clause."
                ),
            }
        )
    if department_id == "compliance" and country == "UK" and not (
        _clause_ok(text or "", _DPA) and _clause_ok(text or "", _UK_GDPR)
    ):
        violations.append(
            {
                "rule_id": "HC-DPA-01",
                "detail": (
                    "Add a Data Processing Agreement (DPA) clause that references UK GDPR "
                    "for this UK client."
                ),
            }
        )
    rule_ids = _unique([item["rule_id"] for item in violations]) if violations else _unique(checked)
    feedback = " ".join(item["detail"] for item in violations)
    return {
        "pass": not violations,
        "rule_ids": rule_ids,
        "violations": violations,
        "contains_phi": phi,
        "feedback": feedback,
    }


def _assemble(department_id: str, parts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    readability = parts["readability"]
    relevance = parts["relevance"]
    compliance = parts["compliance"]
    overall = bool(readability["pass"] and relevance["pass"] and compliance["pass"])
    notes = [
        str(part.get("feedback") or "")
        for part in (readability, relevance, compliance)
        if part.get("feedback")
    ]
    feedback = (
        " ".join(notes)
        if not overall
        else "No changes. Readability, relevance, and the briefing rules passed."
    )
    feedback, _phi = redact(feedback)
    details, _details_phi = redact(str(readability["details"]))
    return {
        "section_id": department_id,
        "department_id": department_id,
        "readability": {
            "pass": bool(readability["pass"]),
            "score": readability["score"],
            "details": details,
        },
        "relevance": {
            "pass": bool(relevance["pass"]),
            "missing_aspects": list(relevance["missing_aspects"]),
        },
        "compliance": {
            "pass": bool(compliance["pass"]),
            "rule_ids": list(compliance["rule_ids"]),
            "violations": list(compliance["violations"]),
        },
        "overall_pass": overall,
        "feedback_for_generator": feedback,
        "contains_phi": bool(compliance["contains_phi"]),
    }


def evaluate_section(
    draft: str,
    *,
    department_id: str,
    metadata: dict[str, Any],
    key_aspects: list[str],
) -> dict[str, Any]:
    """Run the three evaluators at the same time on this section only."""

    def readability() -> dict[str, Any]:
        return check_readability(draft)

    def relevance() -> dict[str, Any]:
        return check_relevance(
            draft,
            department_id=department_id,
            metadata=metadata,
            key_aspects=key_aspects,
        )

    def compliance() -> dict[str, Any]:
        return check_compliance(draft, department_id=department_id, metadata=metadata)

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            "readability": pool.submit(readability),
            "relevance": pool.submit(relevance),
            "compliance": pool.submit(compliance),
        }
        parts = {name: future.result() for name, future in futures.items()}
    return _assemble(department_id, parts)


def evaluate_many(drafts: list[dict[str, Any]], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate every department section at the same time."""

    def _one(item: dict[str, Any]) -> dict[str, Any]:
        result = evaluate_section(
            str(item.get("draft") or ""),
            department_id=str(item["department_id"]),
            metadata=metadata,
            key_aspects=list(item.get("key_aspects") or []),
        )
        return {
            "round": item["round"],
            "department_id": item["department_id"],
            "draft": item.get("draft") or "",
            "result": result,
        }

    if not drafts:
        return []
    with ThreadPoolExecutor(max_workers=len(drafts)) as pool:
        futures = [pool.submit(_one, item) for item in drafts]
        return [future.result() for future in futures]


def phi_hold_result(department_id: str, *, iteration_limit: int) -> dict[str, Any]:
    detail = (
        "Intake flagged patient information. Claire Whitfield must review it "
        "before a draft is written."
    )
    return {
        "section_id": department_id,
        "department_id": department_id,
        "readability": {"pass": False, "score": None, "details": "No draft was written."},
        "relevance": {
            "pass": False,
            "missing_aspects": ["draft withheld until Claire Whitfield reviews the PHI flag"],
        },
        "compliance": {
            "pass": False,
            "rule_ids": ["HC-PHI-01"],
            "violations": [{"rule_id": "HC-PHI-01", "detail": detail}],
        },
        "overall_pass": False,
        "feedback_for_generator": detail,
        "contains_phi": False,
        "review_state": "needs_human_review",
        "provisional": True,
        "iterations_used": 0,
        "iteration_limit": iteration_limit,
    }
