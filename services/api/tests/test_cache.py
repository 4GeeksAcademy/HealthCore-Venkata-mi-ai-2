"""TTL cache + GET list caching. Auth still required; writes invalidate."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.core.response_cache import PRODUCTS_TTL_SECONDS, SUPPLIERS_TTL_SECONDS, response_cache
from app.core.ttl_cache import TtlCache
from app.inventory.service import seed_inventory
from app.load_seed import seed_inventory_load, seed_supplier_load
from tests.test_suppliers import USA_SUPPLIER, UK_SUPPLIER


def test_ttl_cache_expires_and_prefix_invalidation(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = TtlCache()
    clock = {"now": 100.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])

    cache.set("suppliers:list:*:*", ["a"], ttl_seconds=10)
    cache.set("inventory:products", ["b"], ttl_seconds=10)
    assert cache.get("suppliers:list:*:*") == ["a"]

    cache.invalidate_prefix("suppliers:")
    assert cache.get("suppliers:list:*:*") is None
    assert cache.get("inventory:products") == ["b"]

    clock["now"] = 111.0
    assert cache.get("inventory:products") is None


def test_supplier_list_cache_hit_and_write_invalidation(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post("/suppliers", json=USA_SUPPLIER, headers=auth_headers)
    assert created.status_code == 201

    miss = client.get("/suppliers", headers=auth_headers)
    hit = client.get("/suppliers", headers=auth_headers)
    assert miss.status_code == 200
    assert hit.status_code == 200
    assert miss.headers.get("x-cache") == "MISS"
    assert hit.headers.get("x-cache") == "HIT"
    assert miss.json() == hit.json()

    patched = client.patch(
        f"/suppliers/{created.json()['id']}/rate",
        json={"monthly_rate": 1500.0},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    after_write = client.get("/suppliers", headers=auth_headers)
    assert after_write.headers.get("x-cache") == "MISS"
    assert after_write.json()[0]["monthly_rate"] == 1500.0


def test_supplier_filter_keys_do_not_share_entries(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post("/suppliers", json=USA_SUPPLIER, headers=auth_headers)
    client.post("/suppliers", json=UK_SUPPLIER, headers=auth_headers)

    usa = client.get("/suppliers", params={"country": "USA"}, headers=auth_headers)
    uk = client.get("/suppliers", params={"country": "UK"}, headers=auth_headers)
    assert usa.headers.get("x-cache") == "MISS"
    assert uk.headers.get("x-cache") == "MISS"
    assert all(row["country"] == "USA" for row in usa.json())
    assert all(row["country"] == "UK" for row in uk.json())

    usa_hit = client.get("/suppliers", params={"country": "USA"}, headers=auth_headers)
    assert usa_hit.headers.get("x-cache") == "HIT"
    assert usa_hit.json() == usa.json()


def test_supplier_list_still_requires_auth(client: TestClient) -> None:
    response = client.get("/suppliers")
    assert response.status_code == 401


def test_product_list_cache_invalidates_after_inbound(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    miss = client.get("/inventory/products", headers=auth_headers)
    hit = client.get("/inventory/products", headers=auth_headers)
    assert miss.headers.get("x-cache") == "MISS"
    assert hit.headers.get("x-cache") == "HIT"
    gloves = next(row for row in miss.json() if row["sku"] == "HC-PPE-GLV-100")
    assert gloves["current_stock"] == 12

    inbound = client.post(
        "/inventory/orders/inbound",
        json={
            "product_id": gloves["id"],
            "quantity": 8,
            "notes": "Austin restock",
        },
        headers=auth_headers,
    )
    assert inbound.status_code == 201
    refreshed = client.get("/inventory/products", headers=auth_headers)
    assert refreshed.headers.get("x-cache") == "MISS"
    updated = next(row for row in refreshed.json() if row["id"] == gloves["id"])
    assert updated["current_stock"] == 20


def test_outbound_stock_check_ignores_stale_product_list(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    seed_inventory()
    listed = client.get("/inventory/products", headers=auth_headers).json()
    gloves = next(row for row in listed if row["sku"] == "HC-PPE-GLV-100")
    # Simulate a stale cached listing that claims more stock than SQL has.
    response_cache.set(
        "inventory:products",
        [{**row, "current_stock": 9999} for row in listed],
        PRODUCTS_TTL_SECONDS,
    )
    rejected = client.post(
        "/inventory/orders/outbound",
        json={
            "product_id": gloves["id"],
            "quantity": 20,
            "notes": "Attempted over-issue against stale cache",
        },
        headers=auth_headers,
    )
    assert rejected.status_code == 400
    assert "Available: 12" in rejected.json()["detail"]


def test_auth_me_is_not_cached(client: TestClient, auth_headers: dict[str, str]) -> None:
    first = client.get("/auth/me", headers=auth_headers)
    second = client.get("/auth/me", headers=auth_headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("x-cache") is None
    assert second.headers.get("x-cache") is None


def test_load_seed_then_cache_headers(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert seed_supplier_load(30) == 30
    assert seed_inventory_load(5, 8, 4) == 5
    miss = client.get("/suppliers", headers=auth_headers)
    hit = client.get("/suppliers", headers=auth_headers)
    assert miss.headers.get("x-cache") == "MISS"
    assert hit.headers.get("x-cache") == "HIT"
    assert len(miss.json()) == 30

    products_miss = client.get("/inventory/products", headers=auth_headers)
    products_hit = client.get("/inventory/products", headers=auth_headers)
    assert products_miss.headers.get("x-cache") == "MISS"
    assert products_hit.headers.get("x-cache") == "HIT"
    assert len(products_miss.json()) == 5


def test_supplier_ttl_expiry_forces_miss(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    client.post("/suppliers", json=USA_SUPPLIER, headers=auth_headers)
    clock = {"now": 1_000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    miss = client.get("/suppliers", headers=auth_headers)
    assert miss.headers.get("x-cache") == "MISS"
    hit = client.get("/suppliers", headers=auth_headers)
    assert hit.headers.get("x-cache") == "HIT"
    clock["now"] = 1_000.0 + SUPPLIERS_TTL_SECONDS + 0.1
    expired = client.get("/suppliers", headers=auth_headers)
    assert expired.headers.get("x-cache") == "MISS"
