# MCP Server for Company Tools — Evaluation

**Date:** 2026-11-06  
**Rubric:** MCP Server — "What We Will Evaluate" (9 checks)  
**Implementation as of:** [HC-MS7-PLAN-113](../../plans/HC-MS7-PLAN-113-20261106-mcp-oauth-tools-align.md)  
**Plan:** [HC-MS7-PLAN-111](../../plans/HC-MS7-PLAN-111-20261106-mcp-oauth-tools-plan.md)  
**Overall: 8 Pass, 1 Not run.** The Codespaces MCP Playground check was not exercised. This file does not close MS7.

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/MCPServer.md`](../../../docs/Project_Contexts/MCPServer.md) |
| MCP server | [`mcps/healthcore-tools/`](../../../mcps/healthcore-tools/) |
| Agent client | [`services/knowledge_agent/tools/mcp_incidents.py`](../../../services/knowledge_agent/tools/mcp_incidents.py) |
| Incident routes | [`services/api/app/routers/incidents.py`](../../../services/api/app/routers/incidents.py) |
| MCP tests | [`mcps/healthcore-tools/tests/test_mcp_server.py`](../../../mcps/healthcore-tools/tests/test_mcp_server.py) |
| Agent mechanics | [`tests/pipelines/test_agent_graph.py`](../../../tests/pipelines/test_agent_graph.py), [`tests/pipelines/test_agent_tools.py`](../../../tests/pipelines/test_agent_tools.py) |

Saved after human approval on 2026-11-06. Same-day re-evals overwrite this file only. Does not replace [LangGraphExternalTools-20261104](./LangGraphExternalTools-20261104.md).

## Method

- Transport is Streamable HTTP, stateless JSON, path `/healthcore-tools`. OAuth is MCP Auth (`mcpauth`): protected-resource metadata, RS256 bearer checks, scopes `incidents:read`, `incidents:write`, and `inventory:read`. There is no `inventory:write` scope. FastMCP built-in auth is off. The server uses the MCP SDK `FastMCP`.
- `uv run --system-certs pytest mcps/healthcore-tools/tests/test_mcp_server.py tests/pipelines/test_agent_tools.py tests/pipelines/test_agent_graph.py`: **66 passed**.
- The root environment has no FastAPI, so `services/api/tests` was not executed in this run. The MCP suite asserts the Incidents Manager calls against a stand-in that requires `POST /api/incidents`, `PATCH /api/incidents/{id}/status` with a body of only `status`, and `GET`.
- MCP Playground was not opened. This session is local Windows. A local client is not the Codespaces public URL.
- `.env` is gitignored and was not part of the evaluation evidence. Audit lines do not contain tokens or `patient_id`.

## Rubric

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Server lives under `mcps/`, starts, and exposes tools through MCP discovery | Pass | Package `mcps/healthcore-tools`. Streamable HTTP at `/healthcore-tools`. Discovery test lists four tools with names, descriptions, and input schemas. |
| 2 | A client without a valid OAuth access token cannot list or call tools | Pass | Anonymous `POST` returns HTTP 401 with an MCP Auth auth code (`missing_auth_header`, `invalid_auth_header_format`, `missing_bearer_token`, `invalid_token`, `invalid_issuer`, or `invalid_audience`). |
| 3 | Ticket tool creates, updates status via `PATCH /api/incidents/{id}/status`, and queries the real Incidents Manager | Pass | Tools `incident_create`, `incident_update_status`, and `incident_check_status` call those routes. The status body is only `status`. The proof in this run is the MCP stand-in, which rejects any other method, path, or body. The FastAPI incident suite was not executed here. |
| 4 | Inventory tool answers queries and explicitly rejects writes | Pass | `inventory_query` reads `GET /inventory/products`. `create`, `update`, `delete`, and `adjust_stock` return `inventory_write_forbidden` before any inventory HTTP call. |
| 5 | Each tool has a description and schema from discovery, without reading source | Pass | Discovery response carries name, description, and input schema for all four tools. Descriptions name the scope and the route. |
| 6 | Authentication, authorization, and validation errors use distinct codes | Pass | HTTP 401 auth codes, HTTP 403 `missing_required_scopes` (MCP Auth's required-scopes body), and tool code `validation_error`. A token that can list tools and lacks the tool scope receives 403. |
| 7 | One log entry per tool invocation with client, tool, and result | Pass | Logger `healthcore.mcp.audit`, format `tool=%s client=%s subject=%s result=%s`. The discovery test asserts an audit line for each call. Tokens and `patient_id` are not logged. |
| 8 | The agent no longer calls the Incidents Manager directly | Pass | Production ticket lookup is `McpIncidentLookup` via `langchain-mcp-adapters`. `services/knowledge_agent` has no `/api/incidents` client. `GRAPH_VERSION` stays `knowledge-agent/2`. The inventory node still reads the inventory API directly. This ticket required only incidents to move. Mechanics that need a fake ticket result import `tests/pipelines/ticket_lookup_double.py`, which the agent package does not import. |
| 9 | MCP Playground on a public Codespaces forwarded URL | Not run | Not opened in this session. Localhost and the local MCP client do not satisfy this check. |

## Noted limits (accepted in this save)

1. Per-tool scopes return MCP Auth's `missing_required_scopes` response. One global `required_scopes` list is not used, because that list would stop an `incidents:read` client from listing tools.
2. The OAuth 2.1 / OIDC issuer runs in-process (RS256, JWKS, discovery, authorization code with PKCE S256, client credentials). Staff JWTs from `POST /auth/login` are HS256 and are the wrong audience for this resource. The MCP server calls the HealthCore API with `AGENT_SERVICE_EMAIL` / `AGENT_SERVICE_PASSWORD`.
3. The agent sends `mcp-protocol-version`. Set `MCP_STRIP_PROTOCOL_HEADER=1` only on a machine whose HTTP filter corrupts responses that carry that header. The MCP tests on this workstation set it.
4. The resource path is `/healthcore-tools`. A path ending in `/mcp` is rewritten by that same local filter.

## Agent instructions

1. Canonical eval: this file. Official rubric score: **8 Pass, 1 Not run**.
2. Do not mark check 9 as Pass from a local client or from localhost.
3. Same-day re-evals overwrite this file only. Do not append a second `MCPServer-20261106` file.
4. Do not treat this as an MS7 milestone close.
5. Do not rewrite PLAN-111, PLAN-112, PLAN-113, or PLAN-114.
6. The human commits. Do not commit on their behalf. Do not commit `.env`.
