---
stamp: HC-MS7-PLAN-111
sequence: 111
milestone: MS7
date: 2026-11-06
title: MCP Server for Incidents and Inventory (OAuth) Plan
status: planned
phase: planning
summary: >
  Plan for the MCP Server challenge. A Streamable HTTP MCP server under
  mcps/healthcore-tools exposes the existing Incidents Manager and inventory
  service to any authorized client. OAuth is MCP Auth (mcpauth), not FastMCP
  built-in auth. Incident status changes call PATCH /api/incidents/{id}/status
  on the real API. Inventory writes are rejected by name. The coordinator
  agent's ticket node stops calling the Incidents Manager over HTTP and loads
  incident_check_status through langchain-mcp-adapters. RAG versus tool routing
  stays as in PLAN-109. Does not close MS7. Results are not saved until the
  human approves the rubric.
related_paths:
  - docs/Project_Contexts/MCPServer.md
  - mcps/healthcore-tools/
  - services/api/app/routers/incidents.py
  - services/api/app/incidents_store.py
  - services/api/app/models/incidents.py
  - services/knowledge_agent/nodes.py
  - services/knowledge_agent/tools/mcp_incidents.py
  - services/api/requirements.txt
  - pyproject.toml
  - uv.lock
do_not_repeat:
  - Use FastMCP's built-in OAuth, AuthSettings, or RemoteAuthProvider for this server
  - Put the MCP server under services/
  - Install these dependencies with pip install; use uv add
  - Update incident status with a generic PATCH on the incident resource
  - Leave the agent's production ticket path on TicketLookupTool or any direct /api/incidents call
  - Add an inventory write scope or a write that succeeds
  - Return or log patient_id from MCP tools
  - Change receive_question, retrieve, generate_answer, no_context_answer, reject_question, plan_sources routing, or GRAPH_VERSION
  - Index tickets or stock into Qdrant
  - Edit data/, .env, or CONTEXT.md
  - Save memory-bank/evaluations/Results/MCPServer-*.md before human approval
  - Treat a local MCP client run as the Codespaces MCP Playground item
---

# HC-MS7-PLAN-111 — MCP Server for Incidents and Inventory (OAuth)

## Problem

The coordinator agent (PLAN-109) calls the Incidents Manager from inside the graph. The tech lead's brief ([`MCPServer.md`](../../docs/Project_Contexts/MCPServer.md)) requires those capabilities as an independent MCP server, protected by OAuth via MCP Auth, that any authorized client can discover. The agent itself must consume the Incidents Manager only through that server.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Branch | `feature/mcp-oauth-tools` |
| Where | `mcps/healthcore-tools/` (package `healthcore_mcp`). Not under `services/`. |
| Transport | **Streamable HTTP** on `MCP_PUBLIC_URL` (default `http://127.0.0.1:8010`), MCP path `/mcp`. stdio is rejected: the server is for multiple remote clients (other agents, MCP Playground), and a network listener is what makes OAuth necessary. |
| Auth library | **`mcpauth` only.** Protected Resource Metadata, bearer JWT checks, scopes. FastMCP is the MCP SDK and is constructed with no auth helper. |
| Authorization server | Same process, OIDC discovery + JWKS + token endpoint + authorization-code with PKCE (S256) + in-memory dynamic client registration. RS256. Issuer is `MCP_PUBLIC_URL`. Tokens are not HealthCore HS256 JWTs. |
| Resource id | `{MCP_PUBLIC_URL}/mcp`. Audience of access tokens is that URL. |
| Backend | MCP tools call the **existing** API (`HEALTHCORE_API_URL`) with the service-account login (`AGENT_SERVICE_EMAIL` / `AGENT_SERVICE_PASSWORD`). Clients never receive that password. |
| Incident writes on the API | Add `POST /api/incidents` and `PATCH /api/incidents/{id}/status` to the real incident manager. No `PATCH /api/incidents/{id}`. |
| Agent | `lookup_ticket` default is `McpIncidentLookup`, which uses `langchain_mcp_adapters.MultiServerMCPClient` and invokes only the discovered tool `incident_check_status`. Token scope is `incidents:read`. `TicketLookupTool` stays as a test double and is not the production factory. `GRAPH_VERSION` stays `knowledge-agent/2`. Inventory agent node stays a direct read of the inventory API. |
| PHI | `patient_id` may be sent to `POST /api/incidents` because `validate_row` requires it. It is stored by the incident manager, and it is not returned, not logged, and not copied into traces. |

## Scopes (least privilege)

| Scope | Tools |
|-------|--------|
| `incidents:read` | `incident_check_status` |
| `incidents:write` | `incident_create`, `incident_update_status` |
| `inventory:read` | `inventory_query` |

There is no `inventory:write` scope. A token that can call `inventory_query` and then asks for a write still gets `inventory_write_forbidden`. A token that lacks `inventory:read` gets `insufficient_scope` and the tool does not run.

The coordinator agent's client is registered with `incidents:read` only.

## Tools (discovery is the contract)

Each tool has a name, a description that states the scope, the backend route, and what it will not do, plus a Pydantic input and a result model (`ok`, `code`, `message`, payload). An external client must be able to learn this from `tools/list` alone.

| Tool | Backend | Notes |
|------|---------|--------|
| `incident_create` | `POST /api/incidents` | Fields match the incident manager: `incident_id`, `clinic_id`, `country`, `patient_id`, `category`, `status`, optional `satisfaction_score`. Response is `IncidentRecord` (no `patient_id`). |
| `incident_update_status` | `PATCH /api/incidents/{id}/status` | Body is only `{status}` where status is `open`, `closed`, or `discarded`. |
| `incident_check_status` | `GET /api/incidents/{id}` or `GET /api/incidents` | Same filters as the API: `status`, `category`, `clinic_id`, `country`, `limit`. |
| `inventory_query` | `GET /inventory/products` | Input includes `operation`. Only `query` is performed. `create`, `update`, `delete`, and `adjust_stock` return `inventory_write_forbidden` and do not call a write route. |

## Error and exit codes

Request failures are not a generic "error":

| Situation | HTTP | `code` |
|-----------|------|--------|
| Missing or invalid access token | 401 | `invalid_token` |
| Valid token, wrong scope | 403 | `insufficient_scope` |
| Bad tool arguments | 200 tool result | `validation_error` |
| Inventory write attempt | 200 tool result | `inventory_write_forbidden` |
| Unknown incident | 200 tool result | `incident_not_found` |
| Duplicate create | 200 tool result | `incident_conflict` |
| Incidents or inventory API down | 200 tool result | `upstream_error` |

Process exit codes for `python -m healthcore_mcp`:

| Exit | Meaning |
|------|---------|
| 0 | Clean shutdown |
| 1 | Auth configuration missing or rejected (`auth_config`) |
| 2 | Port already in use (`bind_failed`) |
| 3 | Startup validation failed (`startup_validation`) |

## Audit log

Logger `healthcore.mcp.audit`. One line per tool invocation: tool name, OAuth `client_id`, `sub`, result `code`. No access token, no `patient_id`, no clinical free text.

## Agent migration

`services/knowledge_agent/tools/mcp_incidents.py` obtains a client-credentials token and calls the MCP server. Expected failures map to the existing `TicketLookupOutput` statuses so `tool_fallback` and `compose_answer` stay the same. The node does not import `TicketLookupTool`. Routing edges are unchanged. The trace tool name remains `ticket_lookup`.

## Steps

1. `uv add fastmcp mcpauth langchain-mcp-adapters`. Add the adapter to `services/api/requirements.txt` because the API process hosts the agent.
2. Incident manager create + status routes and store methods, with tests.
3. OAuth resource server, four tools, scope gate, audit log, README (transport, scopes, codes, how to run, Playground steps).
4. Agent MCP client and a test that the production factory does not call `/api/incidents`.
5. Pytest for API, MCP (including one flow per tool and a write rejection), and the existing agent mechanics.
6. Implementation stamp. Present the nine evaluation checks in chat. Do not write the Results file until the human approves.

## Playground

MCP Playground must be given a **public GitHub Codespaces forwarded URL**. This workspace is a local Windows checkout, so that item cannot be passed here. Local proof uses the MCP Python client against the Streamable HTTP endpoint. Do not record the Playground item as Pass.

## Agent instructions

1. Implement the table above. Do not switch the server to stdio.
2. Do not enable FastMCP auth. Bearer checks go through `mcpauth`.
3. Status changes go through `PATCH /api/incidents/{id}/status` only.
4. The production ticket node loads `incident_check_status` from the MCP server. Do not point it back at `TicketLookupTool`.
5. Do not bump `GRAPH_VERSION`. Do not re-record traces unless the human asks.
6. Do not save `memory-bank/evaluations/Results/MCPServer-20261106.md` until the human approves the rubric in chat.
7. Do not close MS7 from this work.
