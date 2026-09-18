"""Inventory decisions. Routes require a staff JWT. Stock is computed from orders."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.inventory.models import InboundOrder, MedicalSupply, OutboundOrder
from app.inventory.service import seed_inventory
from tests.conftest import STAFF_EMAIL


def test_inventory_tables_use_readable_names() -> None:
    assert MedicalSupply.__tablename__ == "medical_supply"
    assert InboundOrder.__tablename__ == "inbound_order"
    assert OutboundOrder.__tablename__ == "outbound_order"


def test_list_products_requires_token(client: TestClient) -> None:
    response = client.get("/inventory/products")
    assert response.status_code == 401


def test_list_seeded_products_shows_computed_current_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    response = client.get("/inventory/products", headers=auth_headers)

    assert response.status_code == 200
    rows = response.json()
    gloves = next(row for row in rows if row["sku"] == "HC-PPE-GLV-100")
    pads = next(row for row in rows if row["sku"] == "HC-CLN-PAD-200")
    assert gloves["name"] == "Nitrile exam gloves (box of 100)"
    assert gloves["current_stock"] == 12
    assert gloves["threshold"] == 24
    assert gloves["current_stock"] < gloves["threshold"]
    assert pads["current_stock"] == 80
    assert "stock" not in gloves


def test_create_product_starts_at_zero_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        "/inventory/products",
        json={"name": "Face masks (box of 50)", "sku": "HC-PPE-MSK-050", "threshold": 10},
        headers=auth_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["current_stock"] == 0
    assert body["sku"] == "HC-PPE-MSK-050"

    fetched = client.get(f"/inventory/products/{body['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["current_stock"] == 0


def test_get_product_unknown_id_is_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/inventory/products/9999", headers=auth_headers)
    assert response.status_code == 404


def test_inbound_increases_stock_and_records_user_uuid(
    client: TestClient, auth_headers: dict[str, str], registered_user: dict
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-PPE-GLV-100")

    created = client.post(
        "/inventory/orders/inbound",
        json={
            "product_id": product_id,
            "quantity": 40,
            "notes": "McKesson delivery — Austin clinic restock",
        },
        headers=auth_headers,
    )

    assert created.status_code == 201
    body = created.json()
    assert body["quantity"] == 40
    assert body["product_name"] == "Nitrile exam gloves (box of 100)"
    assert body["user_uuid"] == str(registered_user["user"]["id"])
    assert body["created_by"] == STAFF_EMAIL

    refreshed = client.get("/inventory/products", headers=auth_headers).json()
    gloves = next(row for row in refreshed if row["id"] == product_id)
    assert gloves["current_stock"] == 52


def test_outbound_decreases_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-PPE-GLV-100")

    created = client.post(
        "/inventory/orders/outbound",
        json={
            "product_id": product_id,
            "quantity": 6,
            "notes": "Manchester clinic weekly consumption",
        },
        headers=auth_headers,
    )

    assert created.status_code == 201
    assert created.json()["user_uuid"]

    refreshed = client.get("/inventory/products", headers=auth_headers).json()
    gloves = next(row for row in refreshed if row["id"] == product_id)
    assert gloves["current_stock"] == 6


def test_outbound_rejects_quantity_above_available_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-PPE-GLV-100")

    rejected = client.post(
        "/inventory/orders/outbound",
        json={
            "product_id": product_id,
            "quantity": 20,
            "notes": "Attempted over-issue",
        },
        headers=auth_headers,
    )

    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "Insufficient stock. Available: 12. Requested: 20."

    unchanged = client.get("/inventory/products", headers=auth_headers).json()
    gloves = next(row for row in unchanged if row["id"] == product_id)
    assert gloves["current_stock"] == 12

    history = client.get("/inventory/orders", headers=auth_headers).json()
    over_issue = [
        row
        for row in history
        if row["type"] == "outbound" and row["notes"] == "Attempted over-issue"
    ]
    assert over_issue == []


def test_order_history_lists_inbound_and_outbound(
    client: TestClient, auth_headers: dict[str, str], registered_user: dict
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-CLN-PAD-200")

    client.post(
        "/inventory/orders/inbound",
        json={"product_id": product_id, "quantity": 5, "notes": "Delivery"},
        headers=auth_headers,
    )
    client.post(
        "/inventory/orders/outbound",
        json={"product_id": product_id, "quantity": 2, "notes": "Use"},
        headers=auth_headers,
    )

    history = client.get("/inventory/orders", headers=auth_headers)
    assert history.status_code == 200
    rows = history.json()
    assert {row["type"] for row in rows} >= {"inbound", "outbound"}
    assert all(row["product_name"] for row in rows)
    staff_rows = [row for row in rows if row["notes"] in {"Delivery", "Use"}]
    assert all(row["user_uuid"] == str(registered_user["user"]["id"]) for row in staff_rows)
    assert all(row["created_by"] == STAFF_EMAIL for row in staff_rows)


def test_empty_catalog_and_orders_return_empty_lists(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    products = client.get("/inventory/products", headers=auth_headers)
    orders = client.get("/inventory/orders", headers=auth_headers)

    assert products.status_code == 200
    assert products.json() == []
    assert orders.status_code == 200
    assert orders.json() == []
