"""The agent's tools against the real incident and inventory routes (FastAPI TestClient).

Same tool classes the agent uses in production; only the transport is in-process.
The service account logs in with POST /auth/login like any backend client.
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


def test_ticket_tool_reads_the_incident_manager(tools) -> None:
    pkg, session = tools
    tool = pkg.TicketLookupTool(session)

    one = tool(pkg.TicketLookupInput(ticket_id="INC-0042"))
    open_billing = tool(pkg.TicketLookupInput(status="open", category="BILLING"))
    rejected_row = tool(pkg.TicketLookupInput(ticket_id="INC-0095"))
    missing = tool(pkg.TicketLookupInput(ticket_id="INC-0482"))

    assert (one.status, one.http_status) == ("ok", 200)
    assert one.tickets[0].model_dump(include={"incident_id", "status", "category", "clinic_id"}) == {
        "incident_id": "INC-0042",
        "status": "closed",
        "category": "WORKFORCE",
        "clinic_id": "us-tx-002",
    }
    assert (open_billing.total, [t.incident_id for t in open_billing.tickets]) == (
        6,
        ["INC-0061", "INC-0062", "INC-0063", "INC-0064", "INC-0065"],
    )
    assert (rejected_row.status, missing.status) == ("not_found", "not_found")


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
        pkg.TicketLookupTool(session)(pkg.TicketLookupInput(ticket_id="INC-0042"))
        pkg.TicketLookupTool(session)(pkg.TicketLookupInput(status="open"))
        pkg.InventoryLookupTool(session)(pkg.InventoryLookupInput(product_query="gloves"))

    assert incidents_store.DB_PATH.read_bytes() == incidents_before
    assert client.get("/inventory/products", headers=auth_headers).json() == products_before
    assert client.get("/inventory/orders", headers=auth_headers).json() == orders_before


def test_wrong_service_password_is_an_auth_failure(tools, client: TestClient) -> None:
    pkg, _ = tools
    bad = pkg.ReadOnlyApiSession(pkg.ServiceCredentials("http://testserver", STAFF_EMAIL, "wrong"), client=client)

    assert pkg.TicketLookupTool(bad)(pkg.TicketLookupInput(ticket_id="INC-0042")).status == "auth_failed"
