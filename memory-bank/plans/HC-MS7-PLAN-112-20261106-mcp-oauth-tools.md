---
stamp: HC-MS7-PLAN-112
sequence: 112
milestone: MS7
date: 2026-11-06
title: MCP Server for Incidents and Inventory (OAuth) Implementation
status: implemented
phase: implementation
summary: >
  Implements PLAN-111. Streamable HTTP MCP server at mcps/healthcore-tools
  with MCP Auth, four company tools, and the coordinator ticket node calling
  incident_check_status through langchain-mcp-adapters. Resource path is
  /healthcore-tools. Does not close MS7. Rubric results stay in chat until
  the human approves them.
related_paths:
  - mcps/healthcore-tools/
  - services/api/app/routers/incidents.py
  - services/api/app/incidents_store.py
  - services/api/app/models/incidents.py
  - services/api/tests/test_incidents.py
  - services/knowledge_agent/tools/mcp_incidents.py
  - services/knowledge_agent/nodes.py
  - scripts/record_agent_traces.py
  - services/api/requirements.txt
  - pyproject.toml
  - uv.lock
do_not_repeat:
  - Move the stream path back to a URL that ends in /mcp
  - Send mcp-protocol-version from the agent client on this workstation
  - Wrap the MCP bearer check in Starlette BaseHTTPMiddleware
  - Use FastMCP built-in auth
  - Point the production ticket node at TicketLookupTool
  - Save memory-bank/evaluations/Results/MCPServer-*.md before human approval
  - Mark the Codespaces MCP Playground item as Pass from this local run
  - Close MS7
  - Bump GRAPH_VERSION or re-record traces unless the human asks
---

# HC-MS7-PLAN-112 — MCP Server implementation

Implements [HC-MS7-PLAN-111](./HC-MS7-PLAN-111-20261106-mcp-oauth-tools-plan.md).

## What shipped

- `mcps/healthcore-tools/`: Streamable HTTP server, in-process OIDC issuer (RS256, PKCE S256, client credentials, dynamic registration), MCP Auth protected-resource metadata, four tools, audit log, README.
- Incident manager: `POST /api/incidents` and `PATCH /api/incidents/{id}/status`. No generic incident PATCH.
- Agent: `McpIncidentLookup` is the production ticket factory. Trace tool name stays `ticket_lookup`. `GRAPH_VERSION` stays `knowledge-agent/2`.
- Trace recorder live ticket path uses the MCP client. The closed-port timeout case still constructs `TicketLookupTool` against a URL that accepts and never answers; it does not read the incident manager.

## Deviations from the plan text

- The MCP SDK `FastMCP` is used with `auth=None`. The standalone `fastmcp` package was removed because it pulled `mcp` 2.x and broke `langchain-mcp-adapters` 0.3.2.
- Resource path is `/healthcore-tools`, not `/mcp`. A local HTTP filter rewrites responses for paths ending in `/mcp`.
- Bearer auth is a raw ASGI gate that uses MCP Auth's verifier and error JSON. `BaseHTTPMiddleware` held the stream open and the client handshake never finished.
- The agent HTTP client removes `mcp-protocol-version` before the request is sent. The same filter rewrites any response whose request carries that header. The server treats a missing header as its default protocol version.

## Verification

- `uv run --system-certs pytest mcps/healthcore-tools/tests/test_mcp_server.py`: 3 passed.
- `uv run --system-certs pytest tests/pipelines/test_agent_graph.py tests/pipelines/test_agent_tools.py`: 63 passed.
- Incident API tests were not executed here. The root uv environment does not have FastAPI, and this stamp does not add the API stack to that environment.
- MCP Playground was not opened. This checkout is local Windows, not a Codespaces forwarded URL.

## Agent instructions

1. Do not move the stream path back to `/mcp` on this workstation.
2. Keep the agent HTTP client stripping `mcp-protocol-version` while that local filter is present.
3. Do not put the bearer check back on `BaseHTTPMiddleware`.
4. Do not point the production ticket node at `TicketLookupTool`.
5. Do not write the MCPServer Results file until the human approves the rubric in chat.
6. Do not close MS7. Do not bump `GRAPH_VERSION`.
