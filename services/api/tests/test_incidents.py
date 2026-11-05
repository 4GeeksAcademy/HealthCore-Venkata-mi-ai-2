"""Incident analyze/export decisions (API-042). Routes require a staff JWT."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

VALID_CSV = (
    "incident_id,clinic_id,country,patient_id,category,status,satisfaction_score\n"
    "INC-0001,us-tx-001,US,PAT-0002,APPOINTMENT,closed,4.0\n"
)

HEADER_ONLY_CSV = (
    "incident_id,clinic_id,country,patient_id,category,status,satisfaction_score\n"
)


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
        files={"file": ("bad.csv", b"incident_id,clinic_id\nINC-1,us-tx-001\n", "text/csv")},
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
    response = client.get("/api/incidents/results/export")

    assert response.status_code == 401
    assert client.get("/api/incidents").status_code == 401
    assert client.get("/api/incidents/INC-0001").status_code == 401


SAMPLE_CSV = Path(__file__).resolve().parents[3] / "scripts" / "samples" / "incidents-healthcore.csv"


def _upload(client: TestClient, headers: dict[str, str], body: bytes, name: str = "incidents-healthcore.csv"):
    return client.post("/api/incidents/analyze", headers=headers, files={"file": (name, body, "text/csv")})


def test_upload_stores_only_valid_incidents_for_lookup(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert _upload(client, auth_headers, SAMPLE_CSV.read_bytes()).json()["total_valid"] == 94

    listed = client.get("/api/incidents", headers=auth_headers, params={"limit": 200}).json()
    one = client.get("/api/incidents/inc-0042", headers=auth_headers)
    rejected = client.get("/api/incidents/INC-0095", headers=auth_headers)

    assert listed["total"] == 94 and len(listed["items"]) == 94
    assert one.status_code == 200
    assert one.json() | {"first_recorded_at": "", "updated_at": ""} == {
        "incident_id": "INC-0042",
        "clinic_id": "us-tx-002",
        "country": "US",
        "category": "WORKFORCE",
        "status": "closed",
        "satisfaction_score": 3.5,
        "source_file": "incidents-healthcore.csv",
        "first_recorded_at": "",
        "updated_at": "",
    }
    assert "patient_id" not in one.text and "PAT-" not in json.dumps(listed)
    assert rejected.status_code == 404
    assert rejected.json()["detail"] == "Incident not found."


def test_list_filters_match_the_analyzer_breakdown(client: TestClient, auth_headers: dict[str, str]) -> None:
    _upload(client, auth_headers, SAMPLE_CSV.read_bytes())

    open_billing = client.get(
        "/api/incidents", headers=auth_headers, params={"status": "open", "category": "BILLING"}
    ).json()
    open_all = client.get("/api/incidents", headers=auth_headers, params={"status": "open", "limit": 1}).json()
    bad_status = client.get("/api/incidents", headers=auth_headers, params={"status": "pending"})

    assert open_billing["total"] == 6
    assert [i["incident_id"] for i in open_billing["items"]] == [f"INC-006{n}" for n in range(1, 7)]
    assert open_all["total"] == 24 and len(open_all["items"]) == 1
    assert bad_status.status_code == 422


def test_reupload_updates_status_so_lookups_see_the_latest_value(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    _upload(client, auth_headers, VALID_CSV.encode("utf-8"))
    first = client.get("/api/incidents/INC-0001", headers=auth_headers).json()
    reopened = VALID_CSV.replace("APPOINTMENT,closed,4.0", "APPOINTMENT,open,")
    _upload(client, auth_headers, reopened.encode("utf-8"), name="update.csv")
    second = client.get("/api/incidents/INC-0001", headers=auth_headers).json()

    assert (first["status"], second["status"]) == ("closed", "open")
    assert second["source_file"] == "update.csv"
    assert second["first_recorded_at"] == first["first_recorded_at"]
    assert client.get("/api/incidents", headers=auth_headers).json()["total"] == 1
