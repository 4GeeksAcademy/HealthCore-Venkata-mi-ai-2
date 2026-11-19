"""Part 2 loop: handoff in, drafts and evaluation results out. No PDF conversion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from data.pipelines.rfp_intake.departments import DEPARTMENTS
from data.pipelines.rfp_intake.errors import ModelUnavailable
from data.pipelines.rfp_intake import service, store
from data.pipelines.rfp_response.graph import ResponseDeps
from data.pipelines.rfp_response.runner import execute_response

BAD_DRAFT = (
    "HealthCore will not sign a Business Associate Agreement. "
    "Price in GBP. "
    "Patient name: Jane Doe. "
    "Diagnosis: fracture of the left wrist."
)


@pytest.fixture
def rfp_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "rfp.db"
    monkeypatch.setenv("RFP_DATABASE_URL", "sqlite:///" + db_path.as_posix())
    monkeypatch.setenv("RFP_RAW_DIR", str(tmp_path / "raw"))
    service.reset_engine()
    service.init_schema()
    yield
    service.reset_engine()


def _seed(
    ticket_id: str,
    *,
    country: str = "US",
    currency: str = "USD",
    population: int | None = 800,
    client: str = "Meridian Manufacturing",
    guard: str = "",
    phi: bool = False,
) -> None:
    if country == "UK":
        compliance_aspects = ["The partnership must comply with UK GDPR."]
    else:
        compliance_aspects = ["Vendor must execute a Business Associate Agreement (BAA) in compliance with HIPAA."]
    aspects = {
        "revenue": ["Pricing will be evaluated separately."],
        "clinical": ["Clinical capacity and staffing plan are required."],
        "compliance": compliance_aspects,
    }
    sections = []
    for department_id in ("revenue", "clinical", "compliance"):
        owner = DEPARTMENTS[department_id]
        sections.append(
            {
                "department_id": department_id,
                "owner_name": owner.owner_name,
                "owner_role": owner.owner_role,
                "key_aspects": aspects[department_id],
                "open_questions": [],
                "claims": {},
                "contains_phi": False,
            }
        )
    metadata = {
        "client_name": client,
        "client_country": country,
        "program_type": "occupational_health" if country == "US" else "referral_network",
        "covered_population": population,
        "deadline": "August 23, 2026",
        "budget_range": "",
        "currency": currency,
        "departments_needed": ["revenue", "clinical", "compliance"],
        "open_questions": [],
    }
    handoff = {
        "ticket_id": ticket_id,
        "part": 1,
        "next": "part2_drafting",
        "phi_detected": phi,
        "part2_guard": guard,
        "metadata": metadata,
        "sections": sections,
        "conflicts": [{"field": "covered_population", "resolution": "unresolved_for_part3"}],
        "sales_summary": f"{client} asked for a proposal.",
        "summary_source": "structured",
    }
    store.insert_analyzing(ticket_id=ticket_id, original_filename="request.pdf")
    assert store.save_complete(
        ticket_id,
        phi_detected=phi,
        readability={"word_count": 40, "estimated_tokens": 40, "cost_band": "low"},
        metadata=metadata,
        sections=sections,
        handoff=handoff,
    )


def test_pass_uses_the_handoff_and_does_not_convert_the_pdf(rfp_db, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("pdf")

    monkeypatch.setattr("data.pipelines.rfp_intake.convert.convert_pdf", boom)
    _seed("pass-us")

    def offline(_system: str, _user: str) -> dict:
        raise ModelUnavailable("offline")

    status = execute_response("pass-us", deps=ResponseDeps(complete_json=offline, max_rounds=2))
    view = store.ticket_view("pass-us", stale_after_seconds=900)
    assert view is not None
    assert status == "under_evaluation"
    assert view["status"] == "under_evaluation"
    assert view["part2_outcome"] == "passed"
    assert view["evaluation_closed"] is True
    assert view["handoff_ready"] is True
    assert "drafting" in view["status_trail"]
    assert "under_evaluation" in view["status_trail"]
    assert view["conflicts"][0]["resolution"] == "unresolved_for_part3"
    by_id = {section["department_id"]: section for section in view["sections"]}
    assert set(by_id) == {"revenue", "clinical", "compliance"}
    for section in by_id.values():
        evaluation = section["evaluation"]
        assert evaluation["overall_pass"] is True
        assert evaluation["review_state"] == "passed"
        assert evaluation["readability"]["pass"] is True
        assert evaluation["relevance"]["pass"] is True
        assert evaluation["compliance"]["pass"] is True
        assert section["draft_content"]
        assert "Jane Doe" not in section["draft_content"]
    assert "USD" in by_id["revenue"]["draft_content"]
    assert "GBP" not in by_id["revenue"]["draft_content"]
    assert "Pricing will be evaluated separately." in by_id["revenue"]["draft_content"]
    assert "Business Associate Agreement" in by_id["compliance"]["draft_content"]
    assert "waiting_for_approval" not in json.dumps(view)
    ticket = store.get_ticket("pass-us")
    assert ticket is not None
    assert ticket.handoff_json["part"] == 2
    assert ticket.handoff_json["next"] == "part3_approval"


def test_iteration_limit_keeps_the_last_draft(rfp_db) -> None:
    calls: list[str] = []
    revenue_users: list[str] = []

    def always_bad(system: str, user: str) -> dict:
        calls.append(system)
        if "REVENUE_GENERATOR" in system:
            revenue_users.append(user)
        return {"draft": BAD_DRAFT}

    _seed("limit-us")
    status = execute_response("limit-us", deps=ResponseDeps(complete_json=always_bad, max_rounds=2))
    view = store.ticket_view("limit-us", stale_after_seconds=900)
    assert view is not None
    assert status == "needs_human_review"
    assert view["status"] == "needs_human_review"
    assert view["part2_outcome"] == "needs_human_review"
    assert view["handoff_ready"] is True
    assert view["status"] != "discarded"
    revenue_calls = [system for system in calls if "REVENUE_GENERATOR" in system]
    assert len(revenue_calls) == 2
    assert len(calls) == 6
    assert len(revenue_users) == 2
    first_feedback = revenue_users[0].split("feedback_for_generator:", 1)[1].strip()
    second_feedback = revenue_users[1].split("feedback_for_generator:", 1)[1].strip()
    assert first_feedback == ""
    assert "words" in second_feedback.lower()
    for section in view["sections"]:
        evaluation = section["evaluation"]
        assert evaluation["overall_pass"] is False
        assert evaluation["review_state"] == "needs_human_review"
        assert evaluation["provisional"] is True
        assert evaluation["iterations_used"] == 2
        assert "Jane Doe" not in (section["draft_content"] or "")
        assert "Jane Doe" not in json.dumps(evaluation)
    assert "drafting" in view["status_trail"]
    assert "under_evaluation" in view["status_trail"]
    assert view["status_trail"][-1] == "needs_human_review"
    ticket = store.get_ticket("limit-us")
    assert ticket is not None
    saved = json.dumps(ticket.handoff_json)
    assert "Jane Doe" not in saved
    assert "waiting_for_approval" not in saved
    assert "fracture" not in saved


def test_start_draft_marks_the_ticket_and_returns(rfp_db, monkeypatch: pytest.MonkeyPatch) -> None:
    queued: list[str] = []
    monkeypatch.setattr(service, "enqueue_response", lambda ticket_id: queued.append(ticket_id))
    _seed("queue-us")
    assert service.start_draft("queue-us") == "drafting"
    assert queued == ["queue-us"]
    view = store.ticket_view("queue-us", stale_after_seconds=900)
    assert view is not None
    assert view["status"] == "drafting"
    assert view["status_trail"] == ["drafting"]
    with pytest.raises(ValueError):
        service.start_draft("queue-us")


def test_phi_guard_does_not_draft(rfp_db) -> None:
    def forbidden(_system: str, _user: str) -> dict:
        raise AssertionError("generator")

    _seed("phi-us", guard="phi_review_required", phi=True)
    status = execute_response("phi-us", deps=ResponseDeps(complete_json=forbidden, max_rounds=2))
    view = store.ticket_view("phi-us", stale_after_seconds=900)
    assert view is not None
    assert status == "needs_human_review"
    assert view["part2_outcome"] == "needs_human_review"
    for section in view["sections"]:
        assert section["draft_content"] == ""
        assert section["evaluation"]["compliance"]["pass"] is False
        assert "HC-PHI-01" in section["evaluation"]["compliance"]["rule_ids"]
        assert section["evaluation"]["overall_pass"] is False
    assert view["handoff_ready"] is True
