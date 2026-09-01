"""Supplier directory decisions (API-042). Routes require a staff JWT."""

from __future__ import annotations

from fastapi.testclient import TestClient


USA_SUPPLIER = {
    "name": "QA Medical Supplies",
    "country": "USA",
    "categories": ["MEDICAL_SUPPLIES"],
    "monthly_rate": 1200.5,
    "currency": "USD",
    "status": "active",
}

UK_SUPPLIER = {
    "name": "QA Lab Consumables UK",
    "country": "UK",
    "categories": ["LAB_CONSUMABLES"],
    "monthly_rate": 800.0,
    "currency": "GBP",
    "status": "active",
}


def test_create_and_list_supplier_uses_official_rate_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post("/suppliers", json=USA_SUPPLIER, headers=auth_headers)

    assert created.status_code == 201
    body = created.json()
    assert body["name"] == USA_SUPPLIER["name"]
    assert body["monthly_rate"] == USA_SUPPLIER["monthly_rate"]
    assert body["country"] == "USA"
    assert body["currency"] == "USD"
    assert "contract_rate" not in body

    listed = client.get("/suppliers", headers=auth_headers)
    assert listed.status_code == 200
    assert any(row["id"] == body["id"] for row in listed.json())


def test_list_suppliers_filters_by_country_and_category(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post("/suppliers", json=USA_SUPPLIER, headers=auth_headers)
    client.post("/suppliers", json=UK_SUPPLIER, headers=auth_headers)

    usa_only = client.get("/suppliers", params={"country": "USA"}, headers=auth_headers)
    lab_only = client.get(
        "/suppliers", params={"category": "LAB_CONSUMABLES"}, headers=auth_headers
    )

    assert usa_only.status_code == 200
    assert all(row["country"] == "USA" for row in usa_only.json())
    assert lab_only.status_code == 200
    assert all("LAB_CONSUMABLES" in row["categories"] for row in lab_only.json())


def test_unknown_supplier_is_not_found(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = client.get("/suppliers/9999", headers=auth_headers)
    patch_rate = client.patch(
        "/suppliers/9999/rate", json={"monthly_rate": 10.0}, headers=auth_headers
    )
    patch_status = client.patch(
        "/suppliers/9999/status", json={"status": "suspended"}, headers=auth_headers
    )
    deleted = client.delete("/suppliers/9999", headers=auth_headers)

    assert missing.status_code == 404
    assert patch_rate.status_code == 404
    assert patch_status.status_code == 404
    assert deleted.status_code == 404
    assert missing.json()["detail"] == "Supplier not found."


def test_suppliers_require_authentication(client: TestClient) -> None:
    response = client.get("/suppliers")

    assert response.status_code == 401
