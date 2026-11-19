"""Evaluator agents: readability, relevance, and a briefing compliance rule."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from data.pipelines.rfp_response import evaluators
from data.pipelines.rfp_response.evaluators import (
    check_compliance,
    check_readability,
    check_relevance,
    evaluate_section,
)


def test_short_section_fails_readability() -> None:
    result = check_readability("Price in USD only.")
    assert result["pass"] is False
    assert "words" in result["details"].lower()


def test_relevance_lists_a_missing_aspect() -> None:
    result = check_relevance(
        "Tom Callahan quotes Meridian Manufacturing in USD. " * 8,
        department_id="revenue",
        metadata={"client_name": "Meridian Manufacturing", "client_country": "US", "currency": "USD"},
        key_aspects=["Pricing will be evaluated separately."],
    )
    assert result["pass"] is False
    assert any("Pricing will be evaluated separately" in item for item in result["missing_aspects"])


def test_us_draft_that_refuses_a_baa_fails_compliance() -> None:
    draft = (
        "HealthCore will not sign a Business Associate Agreement. "
        "Pricing for this US client is quoted in GBP. "
        "Patient name: Jane Doe. Diagnosis: fracture of the left wrist."
    )
    result = check_compliance(
        draft,
        department_id="compliance",
        metadata={"client_country": "US", "currency": "USD", "covered_population": 800},
    )
    assert result["pass"] is False
    assert "HC-BAA-01" in result["rule_ids"]


def test_three_evaluators_run_together(monkeypatch) -> None:
    barrier = threading.Barrier(3)

    def wait_then(payload: dict):
        def _inner(*_args, **_kwargs):
            barrier.wait(timeout=2)
            return payload

        return _inner

    monkeypatch.setattr(
        evaluators,
        "check_readability",
        wait_then({"pass": True, "score": 60.0, "details": "ok", "feedback": ""}),
    )
    monkeypatch.setattr(
        evaluators,
        "check_relevance",
        wait_then({"pass": True, "missing_aspects": [], "feedback": ""}),
    )
    monkeypatch.setattr(
        evaluators,
        "check_compliance",
        wait_then(
            {
                "pass": True,
                "rule_ids": ["HC-PHI-01"],
                "violations": [],
                "contains_phi": False,
                "feedback": "",
            }
        ),
    )
    result = evaluate_section(
        "A long enough section for the pool.",
        department_id="revenue",
        metadata={"client_country": "US"},
        key_aspects=[],
    )
    assert result["overall_pass"] is True
    assert result["department_id"] == "revenue"


def test_departments_are_evaluated_together(monkeypatch) -> None:
    barrier = threading.Barrier(3)

    def slow(draft: str, *, department_id: str, metadata: dict, key_aspects: list[str]) -> dict:
        barrier.wait(timeout=2)
        return {
            "section_id": department_id,
            "department_id": department_id,
            "readability": {"pass": True, "score": 60.0, "details": "ok"},
            "relevance": {"pass": True, "missing_aspects": []},
            "compliance": {"pass": True, "rule_ids": ["HC-PHI-01"], "violations": []},
            "overall_pass": True,
            "feedback_for_generator": "No changes. Readability, relevance, and the briefing rules passed.",
            "contains_phi": False,
        }

    monkeypatch.setattr(evaluators, "evaluate_section", slow)
    results = evaluators.evaluate_many(
        [
            {"round": 1, "department_id": "revenue", "draft": "a", "key_aspects": []},
            {"round": 1, "department_id": "clinical", "draft": "b", "key_aspects": []},
            {"round": 1, "department_id": "compliance", "draft": "c", "key_aspects": []},
        ],
        {"client_country": "US"},
    )
    assert {item["department_id"] for item in results} == {"revenue", "clinical", "compliance"}
