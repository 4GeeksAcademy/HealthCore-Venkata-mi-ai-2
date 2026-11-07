"""Inventory tool and the real Incidents Manager routes (FastAPI TestClient).

The agent reads inventory directly. Ticket questions go through the MCP server,
so these tests call the incident routes themselves and do not use a second
ticket client.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from app import incidents_store
from app.inventory.repo import seed_inventory
from app.routers import agent as agent_router
from fastapi.testclient import TestClient

from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD

SAMPLE_CSV = Path(__file__).resolve().parents[3] / "scripts" / "samples" / "incidents-healthcore.csv"


@pytest.fixture
def tools(client: TestClient, auth_headers: dict[str, str]):
    agent_router._agent_package()
    tools_pkg = importlib.import_module("knowledge_agent.tools")
    upload = client.post(
        "/api/incidents/analyze",
        headers=auth_headers,
        files={"file": ("incidents-healthcore.csv", SAMPLE_CSV.read_bytes(), "text/csv")},
    )
    assert upload.status_code == 200
    seed_inventory()
    creds = tools_pkg.ServiceCredentials("http://testserver", STAFF_EMAIL, STAFF_PASSWORD)
    session = tools_pkg.ReadOnlyApiSession(creds, client=client)
    return tools_pkg, session


def test_incident_manager_reads_match_the_routes_the_mcp_server_calls(
    tools, client: TestClient, auth_headers: dict[str, str]
) -> None:
    one = client.get("/api/incidents/INC-0042", headers=auth_headers)
    open_billing = client.get(
        "/api/incidents",
        headers=auth_headers,
        params={"status": "open", "category": "BILLING", "limit": 5},
    )
    missing = client.get("/api/incidents/INC-0482", headers=auth_headers)

    assert one.status_code == 200
    assert one.json()["incident_id"] == "INC-0042"
    assert one.json()["status"] == "closed"
    assert one.json()["category"] == "WORKFORCE"
    assert one.json()["clinic_id"] == "us-tx-002"
    assert "patient_id" not in one.json()
    body = open_billing.json()
    assert (body["total"], [row["incident_id"] for row in body["items"]]) == (
        6,
        ["INC-0061", "INC-0062", "INC-0063", "INC-0064", "INC-0065"],
    )
    assert missing.status_code == 404


def test_inventory_tool_reads_the_inventory_manager(tools, client: TestClient, auth_headers: dict[str, str]) -> None:
    pkg, session = tools
    listed = {p["sku"]: p for p in client.get("/inventory/products", headers=auth_headers).json()}

    output = pkg.InventoryLookupTool(session)(pkg.InventoryLookupInput(product_query="nitrile exam gloves"))

    assert output.status == "ok"
    [gloves] = output.products
    assert gloves.current_stock == listed[gloves.sku]["current_stock"]
    assert gloves.threshold == listed[gloves.sku]["threshold"]


def test_tools_leave_incident_and_inventory_data_unchanged(
    tools, client: TestClient, auth_headers: dict[str, str]
) -> None:
    pkg, session = tools
    incidents_before = incidents_store.DB_PATH.read_bytes()
    products_before = client.get("/inventory/products", headers=auth_headers).json()
    orders_before = client.get("/inventory/orders", headers=auth_headers).json()

    for _ in range(3):
        client.get("/api/incidents/INC-0042", headers=auth_headers)
        client.get("/api/incidents", headers=auth_headers, params={"status": "open"})
        pkg.InventoryLookupTool(session)(pkg.InventoryLookupInput(product_query="gloves"))

    assert incidents_store.DB_PATH.read_bytes() == incidents_before
    assert client.get("/inventory/products", headers=auth_headers).json() == products_before
    assert client.get("/inventory/orders", headers=auth_headers).json() == orders_before


def test_wrong_service_password_is_an_auth_failure(tools, client: TestClient) -> None:
    pkg, _ = tools
    bad = pkg.ReadOnlyApiSession(pkg.ServiceCredentials("http://testserver", STAFF_EMAIL, "wrong"), client=client)

    assert pkg.InventoryLookupTool(bad)(pkg.InventoryLookupInput(product_query="gloves")).status == "auth_failed"
