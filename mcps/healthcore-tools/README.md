# HealthCore company tools

Streamable HTTP MCP server for the Incidents Manager and the inventory catalog. OAuth is [MCP Auth](https://mcp-auth.dev/) (`mcpauth`). The server does not use FastMCP's built-in auth.

## Transport

Streamable HTTP, stateless, JSON responses, path `/healthcore-tools`.

stdio is the wrong fit. This server is for more than one remote client (the coordinator agent, other agents, and the MCP Playground). A network listener is what makes OAuth necessary: every client presents its own access token, and the server can check scopes per tool.

Default public URL: `http://127.0.0.1:8010`. Override with `MCP_PUBLIC_URL`. The protected resource identifier is `{MCP_PUBLIC_URL}/healthcore-tools`. Access tokens use that URL as `aud`.

The path does not end in `/mcp`. On the workstation where this was built, a local HTTP filter rewrites responses whose path ends in `/mcp`, or whose request carries the header `mcp-protocol-version`. It removes `Content-Length` and advertises chunked encoding without chunk framing, so clients hang. The server accepts clients that send the header. Set `MCP_STRIP_PROTOCOL_HEADER=1` only on a machine with that filter. The agent client then omits the header. Elsewhere it sends `mcp-protocol-version` as the MCP spec requires.

## Run

From the repository root, with the API already listening (default `http://127.0.0.1:8001`):

```text
$env:PYTHONPATH = "mcps/healthcore-tools"
$env:MCP_PUBLIC_URL = "http://127.0.0.1:8010"
$env:MCP_AGENT_CLIENT_ID = "healthcore-agent"
$env:MCP_AGENT_CLIENT_SECRET = "choose-a-secret"
$env:MCP_OPS_CLIENT_ID = "healthcore-ops"
$env:MCP_OPS_CLIENT_SECRET = "choose-another-secret"
$env:AGENT_SERVICE_EMAIL = "<staff service account>"
$env:AGENT_SERVICE_PASSWORD = "<password>"
uv run --system-certs python -m healthcore_mcp
```

`MCP_AGENT_*` is registered with scope `incidents:read` only. `MCP_OPS_*` receives `incidents:read`, `incidents:write`, and `inventory:read`. The service account is how the server calls the real API. Clients never see that password.

Exit codes: `0` clean stop, `1` `auth_config` (bad `MCP_PUBLIC_URL`), `2` `bind_failed`, `3` `startup_validation`.

Discovery:

- `GET /.well-known/openid-configuration`
- `GET /.well-known/oauth-authorization-server`
- `GET /.well-known/jwks.json`
- `GET /.well-known/oauth-protected-resource/healthcore-tools`
- `POST /oauth/token` (`client_credentials` or authorization code with PKCE S256)
- `POST /oauth/register`
- `GET` and `POST /oauth/authorize`

## Scopes

| Scope | Tools |
| --- | --- |
| `incidents:read` | `incident_check_status` |
| `incidents:write` | `incident_create`, `incident_update_status` |
| `inventory:read` | `inventory_query` |

There is no `inventory:write` scope. `inventory_query` accepts `operation` values `query`, `create`, `update`, `delete`, and `adjust_stock`, and every value other than `query` returns `inventory_write_forbidden` before any inventory HTTP call.

MCP Auth's `required_scopes` is one list for the whole middleware. Putting every scope there would stop a read-only client from listing tools. Each tool therefore runs that same missing-scope check and returns MCP Auth's `missing_required_scopes` response. A token that can list tools and lacks the tool's scope gets HTTP 403.

## Tools and the real API

| Tool | API |
| --- | --- |
| `incident_create` | `POST /api/incidents` |
| `incident_update_status` | `PATCH /api/incidents/{id}/status` (body is `{"status": ...}` only) |
| `incident_check_status` | `GET /api/incidents/{id}` or `GET /api/incidents` |
| `inventory_query` | `GET /inventory/products` |

`patient_id` is required by the incident manager on create. The tool sends it and never returns it or writes it to the audit log.

## Errors

HTTP 401, from MCP Auth: `missing_auth_header`, `invalid_auth_header_format`, `missing_bearer_token`, `invalid_token`, `invalid_issuer`, `invalid_audience`.

HTTP 403: `missing_required_scopes`.

Tool result `code` (the HTTP call already passed authentication): `ok`, `validation_error`, `inventory_write_forbidden`, `incident_not_found`, `incident_conflict`, `upstream_error`.

One audit line per tool invocation, logger `healthcore.mcp.audit`:

```text
tool=<name> client=<client_id> subject=<subject> result=<code>
```

Tokens and `patient_id` are not logged.

## Agent

The coordinator ticket node loads `incident_check_status` with `langchain-mcp-adapters` (`MultiServerMCPClient`). It does not call `/api/incidents`. Env: `HEALTHCORE_MCP_URL`, `MCP_TOKEN_URL`, `MCP_AGENT_CLIENT_ID`, `MCP_AGENT_CLIENT_SECRET`. The trace tool name stays `ticket_lookup`. `GRAPH_VERSION` stays `knowledge-agent/2`.

## MCP Playground

Point the playground at the public URL of this server (a Codespaces forwarded URL), not `localhost`. This session ran on a local Windows machine and did not open the playground, so that check is not a pass.
