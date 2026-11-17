"""Intake graph: parallel departments, discard isolation, PHI, and contradictions."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from data.pipelines.rfp_intake.errors import ModelUnavailable
from data.pipelines.rfp_intake.graph import REQUIRED_NODES, build_graph
from data.pipelines.rfp_intake.nodes import RfpDeps
from data.pipelines.rfp_intake.runner import execute_ticket
from data.pipelines.rfp_intake import service, store

SAMPLES = REPO / "docs" / "Project_Contexts" / "rfp-requests" / "healthcore"

FORMAL = """
REQUEST FOR PROPOSAL

Meridian Manufacturing operates an 800-employee facility in Austin, Texas.
We are seeking a healthcare partner for on-site occupational health and a corporate wellness program.
Proposal Due Date: August 23, 2026
Vendor must execute a Business Associate Agreement (BAA) in compliance with HIPAA.
Pricing will be evaluated separately.
Clinical capacity and staffing plan are required.
"""

INFORMAL = """
Thames Valley University — United Kingdom

We're looking to set up a referral partnership so our students (around 3,000 on the main campus)
can access specialist care. Could someone put together a proposal for us?
We'll need this to be fully compliant with UK GDPR.
"""

VENDOR = """
Subject: Modernize your EHR with MedFlow

Our unified EHR platform could replace your legacy systems.
Would you be open to a quick call to discuss?
Sales, MedFlow Health Systems
"""

CONTRADICTION = """
Pricing discussion references a covered population of 800 employees in Austin, Texas.
Proposal Due Date: August 23, 2026

Clinical operations would need capacity for 1200 visits a week.
Please also loop in People and Workforce.
"""

PHI_RFP = """
Patient name: Jane Doe
Diagnosis: fracture of the left wrist

Harbor Foods in Austin, Texas wants a wellness proposal for 400 employees.
"""


@pytest.fixture
def rfp_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "rfp.db"
    monkeypatch.setenv("RFP_DATABASE_URL", "sqlite:///" + db_path.as_posix())
    monkeypatch.setenv("RFP_RAW_DIR", str(tmp_path / "raw"))
    service.reset_engine()
    service.init_schema()
    yield
    service.reset_engine()


def _scripted(system: str, user: str) -> dict:
    if "CLASSIFIER" in system:
        if "MedFlow" in user:
            return {
                "is_rfp": False,
                "reason_code": "vendor_pitch",
                "client_role": "seller",
                "rationale": "Vendor is selling software to HealthCore.",
            }
        return {
            "is_rfp": True,
            "reason_code": "institutional_request",
            "client_role": "buyer",
            "rationale": "An institution is asking HealthCore for a proposal.",
        }
    if "METADATA" in system:
        if "Meridian" in user or "1200" in user:
            return {
                "client_name": "Meridian Manufacturing",
                "client_country": "US",
                "program_type": "occupational_health",
                "covered_population": 800,
                "deadline": "August 23, 2026",
                "budget_range": "",
                "currency": "USD",
            }
        if "Thames" in user:
            return {
                "client_name": "Thames Valley University",
                "client_country": "UK",
                "program_type": "referral_network",
                "covered_population": 3000,
                "deadline": "August 28th",
                "budget_range": "",
                "currency": "GBP",
            }
        if "Harbor" in user or "400" in user:
            return {
                "client_name": "Harbor Foods",
                "client_country": "US",
                "program_type": "corporate_wellness",
                "covered_population": 400,
                "deadline": "",
                "budget_range": "",
                "currency": "USD",
            }
        return {
            "client_name": "",
            "client_country": "",
            "program_type": "",
            "covered_population": None,
            "deadline": "",
            "budget_range": "",
            "currency": "",
        }
    if "WORKER" in system:
        if "1200" in user:
            return {
                "key_aspects": ["Capacity would need to cover 1200 visits."],
                "open_questions": [],
                "claims": {
                    "covered_population": 1200,
                    "client_country": "US",
                    "budget_range": None,
                    "currency": "USD",
                },
                "contains_phi": False,
            }
        if "800" in user:
            return {
                "key_aspects": ["Pricing covers 800 employees."],
                "open_questions": [],
                "claims": {
                    "covered_population": 800,
                    "client_country": "US",
                    "budget_range": None,
                    "currency": "USD",
                },
                "contains_phi": False,
            }
        if "3000" in user:
            return {
                "key_aspects": ["Referral network for about 3000 students."],
                "open_questions": [],
                "claims": {
                    "covered_population": 3000,
                    "client_country": "UK",
                    "budget_range": None,
                    "currency": "GBP",
                },
                "contains_phi": False,
            }
        if "400" in user:
            return {
                "key_aspects": ["Wellness proposal for 400 employees."],
                "open_questions": [],
                "claims": {
                    "covered_population": 400,
                    "client_country": "US",
                    "budget_range": None,
                    "currency": "USD",
                },
                "contains_phi": False,
            }
        return {
            "key_aspects": ["Review the passage that names this department."],
            "open_questions": [],
            "claims": {
                "client_country": None,
                "covered_population": None,
                "budget_range": None,
                "currency": None,
            },
            "contains_phi": False,
        }
    if "SYNTHESIZER" in system:
        return {
            "sales_summary": (
                "Ask Tom Callahan about payment terms, Dr. Marcus Reid about capacity, "
                "and Claire Whitfield about the data agreement."
            )
        }
    raise AssertionError("unexpected agent")


def _run(ticket_id: str, markdown: str, complete=_scripted) -> str:
    store.insert_analyzing(ticket_id=ticket_id, original_filename="request.pdf")

    def _convert(_ticket_id: str) -> str:
        return markdown

    deps = RfpDeps(convert_pdf=_convert, complete_json=complete)
    return execute_ticket(ticket_id, deps=deps)


def test_graph_is_dedicated_rfp_intake() -> None:
    compiled = build_graph(RfpDeps(convert_pdf=lambda _ticket: "text", complete_json=_scripted))
    names = set(compiled.get_graph().nodes)
    assert REQUIRED_NODES <= names
    assert "generate_answer" not in names
    assert "retrieve" not in names


def test_formal_and_informal_complete_with_three_departments(rfp_db) -> None:
    assert _run("formal", FORMAL) == "intake_complete"
    assert _run("informal", INFORMAL) == "intake_complete"
    formal = store.ticket_view("formal", stale_after_seconds=900)
    informal = store.ticket_view("informal", stale_after_seconds=900)
    assert formal is not None and informal is not None
    assert [section["department_id"] for section in formal["sections"]] == [
        "revenue",
        "clinical",
        "compliance",
    ]
    assert formal["metadata"]["client_country"] == "US"
    assert formal["metadata"]["currency"] == "USD"
    assert formal["metadata"]["covered_population"] == 800
    assert any("BAA" in aspect or "HIPAA" in aspect for aspect in formal["sections"][2]["key_aspects"])
    assert formal["sections"][0]["owner_name"] == "Tom Callahan"
    assert formal["sections"][1]["owner_name"] == "Dr. Marcus Reid"
    assert formal["sections"][2]["owner_name"] == "Claire Whitfield"
    assert "Tom Callahan" in formal["sales_summary"]
    assert formal["handoff_ready"] is True
    assert informal["metadata"]["client_country"] == "UK"
    assert informal["metadata"]["currency"] == "GBP"
    assert any("GDPR" in aspect or "DPA" in aspect for aspect in informal["sections"][2]["key_aspects"])
    handoff = store.get_ticket("formal")
    assert handoff is not None and handoff.handoff_json["ticket_id"] == "formal"
    assert handoff.handoff_json["sections"][0]["key_aspects"]


def test_vendor_discard_does_not_change_another_ticket(rfp_db) -> None:
    assert _run("kept", FORMAL) == "intake_complete"
    assert _run("dropped", VENDOR) == "discarded"
    kept = store.ticket_view("kept", stale_after_seconds=900)
    dropped = store.ticket_view("dropped", stale_after_seconds=900)
    assert kept is not None and kept["status"] == "intake_complete"
    assert dropped is not None and dropped["status"] == "discarded"
    assert dropped["discard_reason_code"] == "vendor_pitch"
    assert dropped["handoff_ready"] is False
    assert kept["metadata"]["client_name"] == "Meridian Manufacturing"


def test_unknown_department_and_contradiction_stay_unresolved(rfp_db) -> None:
    assert _run("split", CONTRADICTION) == "intake_complete"
    view = store.ticket_view("split", stale_after_seconds=900)
    assert view is not None
    assert [section["department_id"] for section in view["sections"]] == [
        "revenue",
        "clinical",
        "compliance",
    ]
    assert any("People and Workforce" in question for question in view["metadata"]["open_questions"])
    assert view["conflicts"]
    assert view["conflicts"][0]["resolution"] == "unresolved_for_part3"
    assert view["conflicts"][0]["field"] == "covered_population"


def test_phi_is_redacted_before_agents_and_flagged(rfp_db) -> None:
    seen: list[str] = []

    def complete(system: str, user: str) -> dict:
        seen.append(user)
        return _scripted(system, user)

    assert _run("phi", PHI_RFP, complete=complete) == "intake_complete"
    assert all("Jane Doe" not in text for text in seen)
    view = store.ticket_view("phi", stale_after_seconds=900)
    assert view is not None
    assert view["phi_detected"] is True
    assert view["part2_guard"] == "phi_review_required"
    blob = json.dumps(view)
    assert "Jane Doe" not in blob
    assert "fracture of the left wrist" not in blob


def test_model_outage_fails_the_ticket_instead_of_discarding(rfp_db) -> None:
    def complete(system: str, user: str) -> dict:
        raise ModelUnavailable("RuntimeError")

    assert _run("down", FORMAL, complete=complete) == "failed"
    view = store.ticket_view("down", stale_after_seconds=900)
    assert view is not None
    assert view["status"] == "failed"
    assert view["discard_reason_code"] in {None, ""}
    assert view["pipeline_error_code"] == "classifier_unavailable"


def test_stale_analyzing_ticket_becomes_failed_without_clobbering_complete(rfp_db) -> None:
    store.insert_analyzing(ticket_id="stale", original_filename="late.pdf")
    assert store.mark_interrupted_if_stale("stale", 0) is True
    saved = store.save_complete(
        "stale",
        phi_detected=False,
        readability={"word_count": 1, "estimated_tokens": 1, "cost_band": "low"},
        metadata={"client_name": "Should Not Stick", "departments_needed": []},
        sections=[],
        handoff={"ticket_id": "stale"},
    )
    assert saved is False
    view = store.ticket_view("stale", stale_after_seconds=900)
    assert view is not None
    assert view["status"] == "failed"
    assert view["pipeline_error_code"] == "pipeline_interrupted"
    assert view["client_name"] == ""


def test_enqueue_returns_before_the_pipeline_finishes(monkeypatch: pytest.MonkeyPatch) -> None:
    entered = threading.Event()
    release = threading.Event()

    def blocked(ticket_id: str, *, deps=None) -> str:
        entered.set()
        release.wait(2)
        return "analyzing"

    monkeypatch.setattr("data.pipelines.rfp_intake.runner.execute_ticket", blocked)
    service.enqueue("ticket-async")
    assert entered.wait(1)
    release.set()


def test_briefing_pdfs_flow_through_markitdown(rfp_db) -> None:
    from data.pipelines.rfp_intake.paths import absolute_pdf_path

    deps = RfpDeps(complete_json=_scripted)
    expected = {
        "healthcore-request-1.pdf": "intake_complete",
        "healthcore-request-2.pdf": "intake_complete",
        "healthcore-request-3.pdf": "discarded",
    }
    results = {}
    for name, status in expected.items():
        content = (SAMPLES / name).read_bytes()
        ticket_id = store.new_ticket_id()
        destination = absolute_pdf_path(ticket_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        store.insert_analyzing(ticket_id=ticket_id, original_filename=name)
        assert execute_ticket(ticket_id, deps=deps) == status
        results[name] = store.ticket_view(ticket_id, stale_after_seconds=900)

    formal = results["healthcore-request-1.pdf"]
    informal = results["healthcore-request-2.pdf"]
    rejected = results["healthcore-request-3.pdf"]
    assert formal is not None and formal["metadata"]["client_name"] == "Meridian Manufacturing"
    assert formal["metadata"]["covered_population"] == 800
    assert formal["metadata"]["currency"] == "USD"
    assert formal["metadata"]["word_count"] > 30
    assert formal["metadata"]["flesch_kincaid_grade"] is not None
    assert formal["metadata"]["gunning_fog"] is not None
    assert formal["metadata"]["cost_band"] in {"low", "medium", "high"}
    assert [section["owner_name"] for section in formal["sections"]] == [
        "Tom Callahan",
        "Dr. Marcus Reid",
        "Claire Whitfield",
    ]
    assert informal is not None and informal["metadata"]["client_country"] == "UK"
    assert informal["metadata"]["currency"] == "GBP"
    assert rejected is not None and rejected["discard_reason_code"] == "vendor_pitch"
    assert rejected["handoff_ready"] is False
