"""Incident analyze/export decisions (API-042). Routes require a staff JWT."""

from __future__ import annotations

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
