"""Inventory tool and the real Incidents Manager routes (FastAPI TestClient).

The agent reads inventory directly. Ticket questions go through the MCP server,
so these tests call the incident routes themselves and do not use a second
ticket client.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from app.inventory.repo import seed_inventory
from app.routers import agent as agent_router
from fastapi.testclient import TestClient

from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD

SAMPLE_CSV = Path(__file__).resolve().parents[3] / "scripts" / "samples" / "incidents-healthcore.csv"
_SHARED = Path(__file__).resolve().parents[3] / "packages" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from healthcore_incidents import parse_csv_rows, transform_valid_rows  # noqa: E402

from app import incidents_store  # noqa: E402


@pytest.fixture
def tools(client: TestClient, auth_headers: dict[str, str]):
    agent_router._agent_package()
    tools_pkg = importlib.import_module("knowledge_agent.tools")
    rows = parse_csv_rows(SAMPLE_CSV.read_text(encoding="utf-8-sig"))
    transformed, _rejected = transform_valid_rows(rows)
    for payload in transformed:
        incidents_store.seed_incident(payload)
    seed_inventory()
    creds = tools_pkg.ServiceCredentials("http://testserver", STAFF_EMAIL, STAFF_PASSWORD)
    session = tools_pkg.ReadOnlyApiSession(creds, client=client)
    return tools_pkg, session


def test_incident_manager_reads_match_the_routes_the_mcp_server_calls(
    tools, client: TestClient, auth_headers: dict[str, str]
) -> None:
    listed = client.get("/api/incidents", headers=auth_headers, params={"limit": 200})
    assert listed.status_code == 200
    assert listed.json()["total"] == 94
    first_id = listed.json()["items"][0]["id"]

    one = client.get(f"/api/incidents/{first_id}", headers=auth_headers)
    missing = client.get("/api/incidents/missing-ticket-id", headers=auth_headers)
    summary = client.get("/api/incidents/summary", headers=auth_headers)
    open_billing = client.get(
        "/api/incidents",
        headers=auth_headers,
        params={"status": "open", "category": "billing_error", "limit": 50},
    ).json()

    assert one.status_code == 200
    assert one.json()["id"] == first_id
    assert one.json()["origin"] == "customer"
    assert "branch" in one.json()
    assert "patient_id" not in one.json()
    assert open_billing["total"] >= 1
    assert all(
        row["status"] == "open" and row["category"] == "billing_error"
        for row in open_billing["items"]
    )
    assert missing.status_code == 404
    assert summary.json()["by_status"]["open"] == 28
    assert summary.json()["by_status"]["resolved"] == 52
    assert summary.json()["by_category"]["patient_experience"] == 61


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
    before_incidents = client.get("/api/incidents/summary", headers=auth_headers).json()
    before_stock = {
        p["sku"]: p["current_stock"] for p in client.get("/inventory/products", headers=auth_headers).json()
    }

    pkg.InventoryLookupTool(session)(pkg.InventoryLookupInput(product_query="nitrile exam gloves"))

    after_incidents = client.get("/api/incidents/summary", headers=auth_headers).json()
    after_stock = {
        p["sku"]: p["current_stock"] for p in client.get("/inventory/products", headers=auth_headers).json()
    }
    assert after_incidents == before_incidents
    assert after_stock == before_stock
