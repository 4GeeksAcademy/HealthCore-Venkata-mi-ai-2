"""POST /rfp/tickets returns 202 and does not run the graph on the request thread."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture
def rfp_service(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RFP_DATABASE_URL", "sqlite:///" + (tmp_path / "rfp.db").as_posix())
    monkeypatch.setenv("RFP_RAW_DIR", str(tmp_path / "raw"))
    module = importlib.import_module("data.pipelines.rfp_intake.service")
    module.reset_engine()
    module.init_schema()
    yield module
    module.reset_engine()


def test_upload_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/rfp/tickets",
        files={"file": ("healthcore-request-1.pdf", PDF, "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_rejects_non_pdf(client: TestClient, auth_headers: dict, rfp_service) -> None:
    response = client.post(
        "/rfp/tickets",
        headers=auth_headers,
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]
    assert rfp_service.list_tickets() == []


def test_upload_returns_202_and_leaves_the_ticket_analyzing(
    client: TestClient, auth_headers: dict, rfp_service, monkeypatch: pytest.MonkeyPatch
) -> None:
    queued: list[str] = []
    monkeypatch.setattr(rfp_service, "enqueue", lambda ticket_id: queued.append(ticket_id))

    first = client.post(
        "/rfp/tickets",
        headers=auth_headers,
        files={"file": ("healthcore-request-1.pdf", PDF, "application/pdf")},
    )
    second = client.post(
        "/rfp/tickets",
        headers=auth_headers,
        files={"file": ("healthcore-request-3.pdf", PDF, "application/pdf")},
    )
    assert first.status_code == 202
    assert second.status_code == 202
    first_id = first.json()["ticket_id"]
    second_id = second.json()["ticket_id"]
    assert first.json()["status"] == "analyzing"
    assert queued == [first_id, second_id]
    assert first_id != second_id

    detail = client.get(f"/rfp/tickets/{first_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "analyzing"
    assert body["original_filename"] == "healthcore-request-1.pdf"
    assert body["pdf_stored"] is True
    assert "data/raw" not in detail.text
    listed = client.get("/rfp/tickets", headers=auth_headers)
    assert listed.status_code == 200
    assert {row["ticket_id"] for row in listed.json()["tickets"]} == {first_id, second_id}


def test_reprocess_queues_a_failed_ticket(
    client: TestClient, auth_headers: dict, rfp_service, monkeypatch: pytest.MonkeyPatch
) -> None:
    queued: list[str] = []
    monkeypatch.setattr(rfp_service, "enqueue", lambda ticket_id: queued.append(ticket_id))
    created = client.post(
        "/rfp/tickets",
        headers=auth_headers,
        files={"file": ("healthcore-request-1.pdf", PDF, "application/pdf")},
    )
    ticket_id = created.json()["ticket_id"]
    from data.pipelines.rfp_intake import store

    assert store.mark_failed(ticket_id, "pipeline_crashed") is True
    queued.clear()
    response = client.post(f"/rfp/tickets/{ticket_id}/reprocess", headers=auth_headers)
    assert response.status_code == 202
    assert response.json()["status"] == "analyzing"
    assert queued == [ticket_id]
    detail = client.get(f"/rfp/tickets/{ticket_id}", headers=auth_headers)
    assert detail.json()["status"] == "analyzing"
    assert detail.json()["pipeline_error_code"] in {None, ""}


def test_draft_returns_202_for_an_intake_complete_ticket(
    client: TestClient, auth_headers: dict, rfp_service, monkeypatch: pytest.MonkeyPatch
) -> None:
    queued: list[str] = []
    monkeypatch.setattr(rfp_service, "enqueue_response", lambda ticket_id: queued.append(ticket_id))
    from data.pipelines.rfp_intake import store
    from data.pipelines.rfp_intake.departments import DEPARTMENTS

    ticket_id = "draft-ready"
    sections = [
        {
            "department_id": department_id,
            "owner_name": DEPARTMENTS[department_id].owner_name,
            "owner_role": DEPARTMENTS[department_id].owner_role,
            "key_aspects": ["A short aspect."],
            "open_questions": [],
            "claims": {},
            "contains_phi": False,
        }
        for department_id in ("revenue", "clinical", "compliance")
    ]
    metadata = {
        "client_name": "Meridian Manufacturing",
        "client_country": "US",
        "currency": "USD",
        "departments_needed": ["revenue", "clinical", "compliance"],
    }
    store.insert_analyzing(ticket_id=ticket_id, original_filename="request.pdf")
    assert store.save_complete(
        ticket_id,
        phi_detected=False,
        readability={"word_count": 40, "estimated_tokens": 40, "cost_band": "low"},
        metadata=metadata,
        sections=sections,
        handoff={"ticket_id": ticket_id, "metadata": metadata, "sections": sections, "part2_guard": ""},
    )
    response = client.post(f"/rfp/tickets/{ticket_id}/draft", headers=auth_headers)
    assert response.status_code == 202
    assert response.json()["status"] == "drafting"
    assert queued == [ticket_id]
    detail = client.get(f"/rfp/tickets/{ticket_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == "drafting"


def test_draft_rejects_a_ticket_that_is_not_ready(
    client: TestClient, auth_headers: dict, rfp_service
) -> None:
    from data.pipelines.rfp_intake import store

    store.insert_analyzing(ticket_id="still-analyzing", original_filename="request.pdf")
    response = client.post("/rfp/tickets/still-analyzing/draft", headers=auth_headers)
    assert response.status_code == 409
    missing = client.post("/rfp/tickets/missing/draft", headers=auth_headers)
    assert missing.status_code == 404
