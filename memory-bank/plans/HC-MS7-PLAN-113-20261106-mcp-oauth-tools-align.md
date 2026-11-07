---
stamp: HC-MS7-PLAN-113
sequence: 113
milestone: MS7
date: 2026-11-06
title: MCP Server Challenge Alignment
status: implemented
phase: implementation
summary: >
  Closes the gaps found after PLAN-112. The agent package no longer contains
  a direct Incidents Manager client. Per-tool scope failures use MCP Auth's
  missing_required_scopes response. The agent sends mcp-protocol-version
  unless MCP_STRIP_PROTOCOL_HEADER=1. Does not close MS7. Rubric results stay
  in chat until the human approves them.
related_paths:
  - services/knowledge_agent/tools/incidents.py
  - services/knowledge_agent/tools/__init__.py
  - services/knowledge_agent/tools/mcp_incidents.py
  - tests/pipelines/ticket_lookup_double.py
  - tests/pipelines/test_agent_tools.py
  - services/api/tests/test_agent_tools_live_api.py
  - scripts/record_agent_traces.py
  - mcps/healthcore-tools/healthcore_mcp/server.py
  - mcps/healthcore-tools/README.md
do_not_repeat:
  - Put a callable Incidents Manager HTTP client back in services/knowledge_agent
  - Make MCP_STRIP_PROTOCOL_HEADER the default
  - Use FastMCP built-in auth or BaseHTTPMiddleware for the bearer check
  - Move the stream path back to a URL that ends in /mcp
  - Save memory-bank/evaluations/Results/MCPServer-*.md before human approval
  - Mark the Codespaces MCP Playground item as Pass from this local run
  - Close MS7
  - Bump GRAPH_VERSION or re-record traces unless the human asks
---

# HC-MS7-PLAN-113 — Challenge alignment

Follows [HC-MS7-PLAN-112](./HC-MS7-PLAN-112-20261106-mcp-oauth-tools.md).

## What changed

- Removed `TicketLookupTool` from `services/knowledge_agent`. The trace name `ticket_lookup` remains. Graph mechanics that need a fake ticket result import `tests/pipelines/ticket_lookup_double.py`. The trace recorder's outage cases use `McpIncidentLookup` against a closed or silent port.
- A missing tool scope now raises MCP Auth's `MISSING_REQUIRED_SCOPES` and the HTTP body is the one MCP Auth builds for `required_scopes`. One global `required_scopes` list is not used, because that would stop an `incidents:read` client from listing tools.
- `mcp_http_client` sends `mcp-protocol-version`. `MCP_STRIP_PROTOCOL_HEADER=1` omits it on the workstation whose HTTP filter corrupts those responses. The MCP tests set that variable.

## Verification

`uv run --system-certs pytest mcps/healthcore-tools/tests/test_mcp_server.py tests/pipelines/test_agent_tools.py tests/pipelines/test_agent_graph.py`: **66 passed**.

The root environment still has no FastAPI, so `services/api/tests` was not executed. MCP Playground was not opened.

## Agent instructions

1. Do not add a direct `/api/incidents` client under `services/knowledge_agent`.
2. Keep per-tool scope failures on MCP Auth's `missing_required_scopes` response.
3. Leave `MCP_STRIP_PROTOCOL_HEADER` unset except on a machine with the local filter. The MCP tests on that machine set it.
4. Do not write the MCPServer Results file until the human approves the rubric in chat.
5. Do not close MS7. Do not bump `GRAPH_VERSION`.
