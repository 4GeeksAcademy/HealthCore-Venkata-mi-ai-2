"""Inventory decisions. Routes require a staff JWT."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.inventory_store import seed_inventory


def test_list_products_requires_token(client: TestClient) -> None:
    response = client.get("/inventory/products")
    assert response.status_code == 401


def test_list_seeded_products_shows_stock_and_threshold(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    response = client.get("/inventory/products", headers=auth_headers)

    assert response.status_code == 200
    rows = response.json()
    gloves = next(row for row in rows if row["sku"] == "HC-PPE-GLV-100")
    assert gloves["name"] == "Nitrile exam gloves (box of 100)"
    assert gloves["stock"] == 12
    assert gloves["threshold"] == 24
    assert gloves["stock"] < gloves["threshold"]


def test_inbound_increases_stock_and_records_creator(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-PPE-GLV-100")

    created = client.post(
        "/inventory/inbound",
        json={
            "product_id": product_id,
            "quantity": 40,
            "notes": "McKesson delivery — Austin clinic restock",
        },
        headers=auth_headers,
    )

    assert created.status_code == 201
    body = created.json()
    assert body["type"] == "inbound"
    assert body["quantity"] == 40
    assert body["product_name"] == "Nitrile exam gloves (box of 100)"
    assert body["created_by"] == "qa.staff@healthcore.example"

    refreshed = client.get("/inventory/products", headers=auth_headers).json()
    gloves = next(row for row in refreshed if row["id"] == product_id)
    assert gloves["stock"] == 52


def test_outbound_decreases_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-PPE-GLV-100")

    created = client.post(
        "/inventory/outbound",
        json={
            "product_id": product_id,
            "quantity": 6,
            "notes": "Manchester clinic weekly consumption",
        },
        headers=auth_headers,
    )

    assert created.status_code == 201
    assert created.json()["type"] == "outbound"

    refreshed = client.get("/inventory/products", headers=auth_headers).json()
    gloves = next(row for row in refreshed if row["id"] == product_id)
    assert gloves["stock"] == 6


def test_outbound_rejects_quantity_above_available_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-PPE-GLV-100")

    rejected = client.post(
        "/inventory/outbound",
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
    assert gloves["stock"] == 12


def test_order_history_lists_inbound_and_outbound(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    products = client.get("/inventory/products", headers=auth_headers).json()
    product_id = next(row["id"] for row in products if row["sku"] == "HC-CLN-PAD-200")

    client.post(
        "/inventory/inbound",
        json={"product_id": product_id, "quantity": 5, "notes": "Delivery"},
        headers=auth_headers,
    )
    client.post(
        "/inventory/outbound",
        json={"product_id": product_id, "quantity": 2, "notes": "Use"},
        headers=auth_headers,
    )

    history = client.get("/inventory/orders", headers=auth_headers)
    assert history.status_code == 200
    rows = history.json()
    assert {row["type"] for row in rows} == {"inbound", "outbound"}
    assert all(row["product_name"] for row in rows)
    assert all(row["created_by"] == "qa.staff@healthcore.example" for row in rows)


def test_empty_catalog_and_orders_return_empty_lists(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    products = client.get("/inventory/products", headers=auth_headers)
    orders = client.get("/inventory/orders", headers=auth_headers)

    assert products.status_code == 200
    assert products.json() == []
    assert orders.status_code == 200
    assert orders.json() == []
