"""Error and process exit codes for the HealthCore MCP server.

Authentication and authorization codes are the ones MCP Auth puts on the HTTP
response. Tool results use the codes below so a client can tell a bad argument
from a refused inventory write from a missing ticket.
"""

from __future__ import annotations

# HTTP 401 — MCP Auth bearer middleware. The token was missing or not accepted.
AUTH_CODES = frozenset(
    {
        "missing_auth_header",
        "invalid_auth_header_format",
        "missing_bearer_token",
        "invalid_token",
        "invalid_issuer",
        "invalid_audience",
    }
)

# HTTP 403 — the token is valid and does not include the tool's scope.
AUTHORIZATION_CODE = "missing_required_scopes"

# Tool result codes (the HTTP call itself already passed authentication).
VALIDATION_ERROR = "validation_error"
INVENTORY_WRITE_FORBIDDEN = "inventory_write_forbidden"
INCIDENT_NOT_FOUND = "incident_not_found"
INCIDENT_CONFLICT = "incident_conflict"
UPSTREAM_ERROR = "upstream_error"
OK = "ok"

EXIT_OK = 0
EXIT_AUTH_CONFIG = 1
EXIT_BIND_FAILED = 2
EXIT_STARTUP_VALIDATION = 3
