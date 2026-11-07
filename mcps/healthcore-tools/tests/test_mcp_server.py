"""MCP server flows: discovery, OAuth, each tool, and a refused inventory write."""

from __future__ import annotations

import inspect
import json
import logging
import os
import socket
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

os.environ["MCP_STRIP_PROTOCOL_HEADER"] = "1"

_PKG = Path(__file__).resolve().parents[1]
_REPO = Path(__file__).resolve().parents[3]
for path in (_PKG, _REPO):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from healthcore_mcp.errors import AUTH_CODES, AUTHORIZATION_CODE  # noqa: E402
from healthcore_mcp.oauth import OAuthClient  # noqa: E402
from healthcore_mcp.server import STREAM_PATH, Settings, _port_is_free, create_app  # noqa: E402
from healthcore_mcp.backend import HealthCoreApi, ServiceAccount  # noqa: E402
from services.knowledge_agent.nodes import AgentDependencies  # noqa: E402
from services.knowledge_agent.tools.contracts import TicketLookupInput  # noqa: E402
from services.knowledge_agent.tools.mcp_incidents import McpIncidentLookup, mcp_http_client  # noqa: E402

INCIDENT = {
    "incident_id": "INC-0042",
    "clinic_id": "us-tx-002",
    "country": "US",
    "category": "WORKFORCE",
    "status": "closed",
    "satisfaction_score": 4.0,
    "source_file": "api",
    "first_recorded_at": "2026-11-06T00:00:00+00:00",
    "updated_at": "2026-11-06T00:00:00+00:00",
}


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture
def mcp_server():
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path
        if path == "/auth/login":
            return httpx.Response(200, json={"access_token": "staff-token"})
        if request.method == "POST" and path == "/api/incidents":
            body = json.loads(request.content)
            created = {**INCIDENT, "incident_id": body["incident_id"], "status": body["status"], "category": body["category"]}
            return httpx.Response(201, json=created)
        if request.method == "PATCH" and path == "/api/incidents/INC-0042/status":
            body = json.loads(request.content)
            assert list(body) == ["status"]
            return httpx.Response(200, json={**INCIDENT, "status": body["status"]})
        if request.method == "GET" and path == "/api/incidents/INC-0042":
            return httpx.Response(200, json=INCIDENT)
        if request.method == "GET" and path == "/api/incidents/INC-4040":
            return httpx.Response(404, json={"detail": "Incident not found."})
        if request.method == "GET" and path == "/api/incidents":
            return httpx.Response(200, json={"total": 1, "items": [INCIDENT]})
        if path == "/inventory/products":
            assert request.method == "GET"
            return httpx.Response(
                200,
                json=[{"id": 1, "name": "Nitrile exam gloves", "sku": "PPE-GLV-100", "category": "ppe", "current_stock": 12, "threshold": 20}],
            )
        return httpx.Response(500, json={"detail": f"unexpected {request.method} {path}"})

    account = ServiceAccount(base, "agent@healthcore.example", "secret")
    api = HealthCoreApi(account, httpx.Client(transport=httpx.MockTransport(handle), base_url="http://company.test"))
    settings = Settings(
        public_url=base,
        host="127.0.0.1",
        port=port,
        clients={
            "agent": OAuthClient("agent", "agent-secret", frozenset({"incidents:read"})),
            "ops": OAuthClient("ops", "ops-secret", frozenset({"incidents:read", "incidents:write", "inventory:read"})),
            "stock": OAuthClient("stock", "stock-secret", frozenset({"inventory:read"})),
        },
    )
    app = create_app(settings, api)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info"))
    errors: list[BaseException] = []

    def _run() -> None:
        try:
            server.run()
        except BaseException as exc:  # noqa: BLE001 — surface thread crashes in the test
            errors.append(exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    last_error = ""
    while time.time() < deadline:
        if errors:
            raise RuntimeError("MCP server thread crashed") from errors[0]
        try:
            response = httpx.get(f"{base}/.well-known/openid-configuration", timeout=1)
            if response.status_code == 200:
                break
            last_error = response.text
        except Exception as exc:  # noqa: BLE001 — startup probe
            last_error = str(exc)
        time.sleep(0.05)
    else:
        raise RuntimeError(f"MCP server did not start: {last_error}")
    yield base, seen
    server.should_exit = True
    thread.join(5)


def _token(base: str, client_id: str, secret: str, scope: str) -> str:
    response = httpx.post(
        f"{base}/oauth/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret, "scope": scope},
        timeout=5,
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _tool_json(result) -> dict:
    text = result.content[0].text
    return json.loads(text)


def test_discovery_auth_and_each_tool(mcp_server, caplog) -> None:
    import asyncio

    asyncio.run(_discovery_auth_and_each_tool(mcp_server, caplog))


async def _discovery_auth_and_each_tool(mcp_server, caplog) -> None:
    base, seen = mcp_server
    caplog.set_level(logging.INFO, logger="healthcore.mcp.audit")
    metadata = httpx.get(f"{base}/.well-known/oauth-protected-resource{STREAM_PATH}", timeout=5)
    oidc = httpx.get(f"{base}/.well-known/openid-configuration", timeout=5)
    anonymous = httpx.post(f"{base}{STREAM_PATH}", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, timeout=5)

    assert metadata.status_code == 200
    assert metadata.json()["resource"] == f"{base}{STREAM_PATH}"
    assert set(metadata.json()["scopes_supported"]) == {"incidents:read", "incidents:write", "inventory:read"}
    assert metadata.json()["authorization_servers"] == [base]
    assert "S256" in oidc.json()["code_challenge_methods_supported"]
    assert anonymous.status_code == 401
    assert anonymous.json()["error"] in AUTH_CODES

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    ops = _token(base, "ops", "ops-secret", "incidents:read incidents:write inventory:read")
    async with streamablehttp_client(
        f"{base}{STREAM_PATH}",
        headers={"Authorization": f"Bearer {ops}"},
        httpx_client_factory=mcp_http_client,
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            by_name = {tool.name: tool for tool in listed.tools}
            assert set(by_name) == {"incident_create", "incident_update_status", "incident_check_status", "inventory_query"}
            assert "PATCH /api/incidents/{id}/status" in by_name["incident_update_status"].description
            assert "incidents:read" in by_name["incident_check_status"].description
            assert "inventory_write_forbidden" in by_name["inventory_query"].description
            assert "patient_id" in by_name["incident_create"].description
            operation = by_name["inventory_query"].inputSchema["properties"]["operation"]
            assert set(operation["enum"]) == {"query", "create", "update", "delete", "adjust_stock"}

            created = _tool_json(
                await session.call_tool(
                    "incident_create",
                    {
                        "incident_id": "INC-8802",
                        "clinic_id": "us-tx-001",
                        "country": "US",
                        "patient_id": "PAT-8802",
                        "category": "BILLING",
                        "status": "open",
                    },
                )
            )
            updated = _tool_json(
                await session.call_tool(
                    "incident_update_status",
                    {"incident_id": "INC-0042", "status": "closed"},
                )
            )
            checked = _tool_json(await session.call_tool("incident_check_status", {"ticket_id": "INC-0042"}))
            missing = _tool_json(await session.call_tool("incident_check_status", {"ticket_id": "INC-4040"}))
            stock = _tool_json(
                await session.call_tool("inventory_query", {"operation": "query", "product_query": "nitrile exam gloves"})
            )
            before_write = len(seen)
            refused = _tool_json(
                await session.call_tool("inventory_query", {"operation": "delete", "product_query": "nitrile exam gloves"})
            )
            bad = _tool_json(await session.call_tool("incident_update_status", {"incident_id": "482", "status": "closed"}))

    assert created["code"] == "ok" and "patient_id" not in created["incident"]
    assert updated["code"] == "ok" and updated["incident"]["status"] == "closed"
    assert checked["code"] == "ok" and checked["incident"]["incident_id"] == "INC-0042"
    assert missing["code"] == "incident_not_found"
    assert stock["code"] == "ok" and stock["products"][0]["current_stock"] == 12
    assert refused["code"] == "inventory_write_forbidden"
    assert bad["code"] == "validation_error"
    assert len(seen) == before_write
    methods = {(request.method, request.url.path) for request in seen}
    assert ("PATCH", "/api/incidents/INC-0042/status") in methods
    assert ("POST", "/api/incidents") in methods
    assert ("GET", "/inventory/products") in methods
    assert not any(request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/inventory") for request in seen)
    audit = [record.getMessage() for record in caplog.records if record.name == "healthcore.mcp.audit"]
    assert any("tool=incident_check_status" in line and "client=ops" in line and "result=ok" in line for line in audit)
    assert any("result=inventory_write_forbidden" in line for line in audit)
    assert all("PAT-8802" not in line for line in audit)

    stock_token = _token(base, "stock", "stock-secret", "inventory:read")
    forbidden = httpx.post(
        f"{base}{STREAM_PATH}",
        headers={"Authorization": f"Bearer {stock_token}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "incident_create", "arguments": {}}},
        timeout=5,
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"] == AUTHORIZATION_CODE


def test_agent_ticket_node_uses_the_mcp_server(mcp_server) -> None:
    base, seen = mcp_server
    before = len(seen)
    lookup = McpIncidentLookup(
        mcp_url=f"{base}{STREAM_PATH}",
        token_url=f"{base}/oauth/token",
        client_id="agent",
        client_secret="agent-secret",
        resource=f"{base}{STREAM_PATH}",
    )
    output = lookup(TicketLookupInput(ticket_id="INC-0042"))

    assert output.status == "ok"
    assert output.endpoint == "mcp:incident_check_status"
    assert output.tickets[0].status == "closed"
    assert output.tickets[0].category == "WORKFORCE"
    assert any(request.method == "GET" and request.url.path == "/api/incidents/INC-0042" for request in seen[before:])
    source = inspect.getsource(McpIncidentLookup)
    assert "MultiServerMCPClient" in source
    assert "/api/incidents" not in source
    assert isinstance(AgentDependencies().lookup_ticket, McpIncidentLookup)
    assert "TicketLookupTool" not in inspect.getsource(
        __import__("services.knowledge_agent.nodes", fromlist=["make_ticket_node"]).make_ticket_node
    )


def test_bad_public_url_and_busy_port(monkeypatch) -> None:
    monkeypatch.setenv("MCP_PUBLIC_URL", "not-a-url")
    from healthcore_mcp.server import ConfigError, Settings as EnvSettings

    with pytest.raises(ConfigError):
        EnvSettings.from_env()
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    try:
        assert _port_is_free("127.0.0.1", sock.getsockname()[1]) is False
    finally:
        sock.close()
