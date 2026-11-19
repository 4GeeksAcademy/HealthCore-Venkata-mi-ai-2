"""Department generators stay separate and draft from the handoff only."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from data.pipelines.rfp_intake.errors import ModelUnavailable
from data.pipelines.rfp_response.evaluators import check_compliance, check_readability, check_relevance
from data.pipelines.rfp_response.generators import (
    GENERATORS,
    compliance_template,
    generate_section,
    revenue_template,
)


def test_each_department_has_its_own_generator() -> None:
    assert set(GENERATORS) == {"revenue", "clinical", "compliance"}
    assert len({GENERATORS[name].system for name in GENERATORS}) == 3
    assert "REVENUE_GENERATOR" in GENERATORS["revenue"].system
    assert "CLINICAL_GENERATOR" not in GENERATORS["revenue"].system
    assert "COMPLIANCE_GENERATOR" not in GENERATORS["revenue"].system


def test_revenue_generator_quotes_usd_and_does_not_invent_a_population() -> None:
    metadata = {
        "client_name": "Meridian Manufacturing",
        "client_country": "US",
        "program_type": "occupational_health",
        "covered_population": None,
        "deadline": "",
        "budget_range": "",
        "currency": "USD",
    }
    section = {
        "key_aspects": ["Pricing will be evaluated separately."],
        "open_questions": ["What is the covered population?"],
    }

    def unavailable(system: str, user: str) -> dict:
        raise ModelUnavailable("offline")

    draft = generate_section(
        "revenue",
        metadata=metadata,
        section=section,
        feedback="",
        complete=unavailable,
    )
    assert draft == revenue_template(metadata, section)
    assert "USD" in draft
    assert "GBP" not in draft
    assert "Meridian Manufacturing" in draft
    assert "Pricing will be evaluated separately." in draft
    assert "employees" not in draft.lower()
    assert "open question" in draft.lower()


def test_generator_sends_feedback_only_to_that_department() -> None:
    seen: dict[str, str] = {}

    def capture(system: str, user: str) -> dict:
        seen["system"] = system
        seen["user"] = user
        return {"draft": "Revenue section placeholder."}

    generate_section(
        "revenue",
        metadata={"client_name": "Meridian Manufacturing", "client_country": "US", "currency": "USD"},
        section={"key_aspects": ["Pricing will be evaluated separately."], "open_questions": []},
        feedback="Quote USD and cover the pricing note.",
        complete=capture,
    )
    assert "REVENUE_GENERATOR" in seen["system"]
    assert "CLINICAL_GENERATOR" not in seen["system"]
    assert "Quote USD and cover the pricing note." in seen["user"]
    assert "raw_pdf" not in seen["user"]
    assert "markdown" not in seen["user"]


def test_uk_compliance_template_requires_a_dpa() -> None:
    text = compliance_template(
        {
            "client_name": "Thames Valley University",
            "client_country": "UK",
            "currency": "GBP",
            "program_type": "referral_network",
            "covered_population": 3000,
        },
        {"key_aspects": ["The partnership must comply with UK GDPR."], "open_questions": []},
    )
    assert "Data Processing Agreement" in text
    assert "UK GDPR" in text
    assert "Business Associate Agreement" not in text
    assert "Thames Valley University" in text
    metadata = {
        "client_name": "Thames Valley University",
        "client_country": "UK",
        "currency": "GBP",
        "program_type": "referral_network",
        "covered_population": 3000,
    }
    assert check_readability(text)["pass"] is True
    assert check_relevance(
        text,
        department_id="compliance",
        metadata=metadata,
        key_aspects=["The partnership must comply with UK GDPR."],
    )["pass"] is True
    compliance = check_compliance(text, department_id="compliance", metadata=metadata)
    assert compliance["pass"] is True
