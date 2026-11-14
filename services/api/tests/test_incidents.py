"""Incident manager and CSV analyze/export tests. Routes require a staff JWT."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

SAMPLE_CSV = Path(__file__).resolve().parents[3] / "scripts" / "samples" / "incidents-healthcore.csv"

VALID_CSV = (
    "incident_id,date,clinic_id,country,category,description,status,patient_id,satisfaction_score\n"
    "HC-900001,2024-01-13,US-TX-02,US,APPOINTMENT,Patient waited over forty five minutes,CLOSED,PAT-900001,4\n"
)

HEADER_ONLY_CSV = (
    "incident_id,date,clinic_id,country,category,description,status,patient_id,satisfaction_score\n"
)

_NEW = {
    "title": "Billing portal timeout",
    "description": "Staff cannot submit claims from Houston Medical Center.",
    "category": "it_system",
    "status": "open",
    "origin": "branch",
    "branch": "houston_med_center",
}


def test_analyze_valid_csv_then_export(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    analyze = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("incidents.csv", VALID_CSV.encode("utf-8"), "text/csv")},
    )

    assert analyze.status_code == 200
    body = analyze.json()
    assert body["total_processed"] == 1
    assert body["total_valid"] == 1

    export = client.get("/api/incidents/results/export", headers=auth_headers)
    assert export.status_code == 200
    assert "total_processed" in export.text


def test_analyze_rejects_empty_or_header_only_csv(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    empty = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    header_only = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("header.csv", HEADER_ONLY_CSV.encode("utf-8"), "text/csv")},
    )

    assert empty.status_code == 400
    assert empty.json()["detail"] == "File is empty."
    assert header_only.status_code == 400
    assert header_only.json()["detail"] == "CSV contains no data rows."


def test_analyze_rejects_non_csv_and_missing_columns(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    not_csv = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    bad_header = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("bad.csv", b"incident_id,clinic_id\nINC-1,US-TX-01\n", "text/csv")},
    )

    assert not_csv.status_code == 400
    assert not_csv.json()["detail"] == "Incorrect format: upload a .csv file."
    assert bad_header.status_code == 400
    assert bad_header.json()["detail"].startswith("Incorrect CSV format:")


def test_export_without_prior_analyze_has_no_results(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/incidents/results/export", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "No analysis results available. Upload a CSV first."


def test_incidents_require_authentication(client: TestClient) -> None:
    assert client.get("/api/incidents/results/export").status_code == 401
    assert client.get("/api/incidents").status_code == 401
    assert client.get("/api/incidents/summary").status_code == 401
    assert client.post("/api/incidents", json=_NEW).status_code == 401


def test_sample_csv_analyze_metrics(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("incidents-healthcore.csv", SAMPLE_CSV.read_bytes(), "text/csv")},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["total_processed"] == 100
    assert body["total_valid"] == 94
    assert body["total_invalid"] == 6
    assert body["avg_satisfaction_closed"] == 3.58
    assert body["by_status"]["OPEN"] == 28
    assert body["by_status"]["CLOSED"] == 52
    assert body["by_status"]["DISCARDED"] == 14


def test_create_list_summary_and_lifecycle(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    empty_summary = client.get("/api/incidents/summary", headers=auth_headers)
    assert empty_summary.status_code == 200
    assert empty_summary.json()["total"] == 0
    assert empty_summary.json()["by_status"]["open"] == 0

    created = client.post("/api/incidents", headers=auth_headers, json=_NEW)
    assert created.status_code == 201, created.text
    record = created.json()
    assert "patient_id" not in record
    assert record["status"] == "open"
    assert record["origin"] == "branch"
    assert record["branch"] == "houston_med_center"
    incident_id = record["id"]

    listed = client.get(
        "/api/incidents",
        headers=auth_headers,
        params={"status": "open", "origin": "branch", "branch": "houston_med_center"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    bad_transition = client.patch(
        f"/api/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "resolved"},
    )
    assert bad_transition.status_code == 400
    assert bad_transition.json()["detail"]["field"] == "status"

    progress = client.patch(
        f"/api/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "in_progress"},
    )
    assert progress.status_code == 200
    assert progress.json()["status"] == "in_progress"

    resolved = client.patch(
        f"/api/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "resolved"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    final = client.patch(
        f"/api/incidents/{incident_id}/status",
        headers=auth_headers,
        json={"status": "discarded"},
    )
    assert final.status_code == 400

    one = client.get(f"/api/incidents/{incident_id}", headers=auth_headers)
    assert one.status_code == 200
    assert one.json()["title"] == "Billing portal timeout"
    assert "patient_id" not in json.dumps(one.json())

    missing = client.get("/api/incidents/does-not-exist", headers=auth_headers)
    assert missing.status_code == 404


def test_create_validation_identifies_field(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    blank = client.post(
        "/api/incidents",
        headers=auth_headers,
        json={**_NEW, "title": "   "},
    )
    assert blank.status_code == 400
    assert blank.json()["detail"]["field"] == "title"


def test_status_patch_unknown_incident_is_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = client.patch(
        "/api/incidents/missing-id/status",
        headers=auth_headers,
        json={"status": "in_progress"},
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Incident not found."
