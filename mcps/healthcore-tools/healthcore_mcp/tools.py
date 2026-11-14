"""Company tools. Names, descriptions, and schemas are the discovery contract.

An external agent should be able to read ``tools/list`` and know what it may
call, which scope it needs, and which HealthCore route will run. Inventory
writes are in the schema on purpose: the server rejects them.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from .backend import HealthCoreApi, UpstreamError
from .errors import (
    AUTHORIZATION_CODE,
    INCIDENT_CONFLICT,
    INCIDENT_NOT_FOUND,
    INVENTORY_WRITE_FORBIDDEN,
    OK,
    UPSTREAM_ERROR,
    VALIDATION_ERROR,
)

audit_log = logging.getLogger("healthcore.mcp.audit")

STATUSES = frozenset({"open", "in_progress", "resolved", "discarded"})
ORIGINS = frozenset({"customer", "branch", "internal"})
CATEGORIES = frozenset(
    {
        "clinical_equipment",
        "it_system",
        "billing_error",
        "compliance_breach",
        "patient_experience",
        "staff_issue",
        "facility_issue",
        "referral_issue",
        "other",
    }
)
BRANCHES = frozenset(
    {
        "central",
        "austin_north",
        "dallas_uptown",
        "houston_med_center",
        "san_antonio_west",
        "miami_brickell",
        "miami_doral",
        "orlando_east",
        "tampa_bay",
        "atlanta_midtown",
        "savannah",
        "london_city",
        "london_west",
        "manchester_central",
    }
)
INCIDENT_FIELDS = (
    "id",
    "title",
    "description",
    "category",
    "status",
    "origin",
    "branch",
    "created_at",
    "updated_at",
)
WRITE_OPERATIONS = frozenset({"create", "update", "delete", "adjust_stock"})

TOOL_SCOPES = {
    "incident_create": ("incidents:write",),
    "incident_update_status": ("incidents:write",),
    "incident_check_status": ("incidents:read",),
    "inventory_query": ("inventory:read",),
}

CREATE_DESCRIPTION = (
    "Create one Incidents Manager ticket. Requires scope incidents:write. "
    "Calls POST /api/incidents on the HealthCore API. Fields: title, description, "
    "category (manager snake_case values such as billing_error or patient_experience), "
    "origin (customer, branch, internal), branch (clinic branch slug including central), "
    "and optional status (open or in_progress). The API generates id and timestamps. "
    "Do not send patient identifiers. Status changes later use incident_update_status."
)
UPDATE_DESCRIPTION = (
    "Change only the status of an existing Incidents Manager ticket. Requires scope "
    "incidents:write. Calls PATCH /api/incidents/{id}/status with a body of {status} "
    "and nothing else. Lifecycle: open→in_progress|discarded; in_progress→resolved|discarded; "
    "resolved and discarded are final. Unknown ids return code incident_not_found."
)
CHECK_DESCRIPTION = (
    "Read Incidents Manager tickets. Requires scope incidents:read. "
    "Calls GET /api/incidents/{id} when ticket_id is set, otherwise GET /api/incidents "
    "with optional filters status, category, origin, branch, and limit (1-50). "
    "Provide a ticket_id or at least one filter. This tool never creates or updates. "
    "Responses never include patient identifiers. Unknown ids return code incident_not_found."
)
INVENTORY_DESCRIPTION = (
    "Read clinic inventory stock. Requires scope inventory:read. "
    "operation=query calls GET /inventory/products and returns name, sku, category, "
    "current_stock, threshold, and below_threshold for matches. "
    "operation values create, update, delete, and adjust_stock are rejected with code "
    "inventory_write_forbidden. The server does not omit the write; it refuses it, "
    "and there is no inventory:write scope. No stock number is changed."
)


class ToolResult(BaseModel):
    """Every tool returns this shape. ``code`` is ok or one of the documented error codes."""

    ok: bool
    code: str
    message: str
    incident: dict[str, Any] | None = None
    incidents: list[dict[str, Any]] | None = None
    total: int | None = None
    products: list[dict[str, Any]] | None = None


def register_tools(mcp: Any, api: HealthCoreApi, auth_info) -> None:
    """Attach the four tools. ``auth_info`` is ``mcp_auth.auth_info``."""

    def finish(tool: str, result: ToolResult) -> dict[str, Any]:
        info = auth_info()
        audit_log.info(
            "tool=%s client=%s subject=%s result=%s",
            tool,
            getattr(info, "client_id", None) or "unknown",
            getattr(info, "subject", None) or "unknown",
            result.code,
        )
        return result.model_dump()

    def denied(tool: str) -> dict[str, Any] | None:
        info = auth_info()
        needed = TOOL_SCOPES[tool]
        scopes = set(getattr(info, "scopes", None) or [])
        if info is None or not scopes.issuperset(needed):
            return finish(
                tool,
                ToolResult(
                    ok=False,
                    code=AUTHORIZATION_CODE,
                    message=f"This tool requires scope {' '.join(needed)}.",
                ),
            )
        return None

    @mcp.tool(name="incident_create", description=CREATE_DESCRIPTION)
    def incident_create(
        title: str = Field(description="Short incident title."),
        description: str = Field(description="Detailed description. Do not include patient identifiers."),
        category: str = Field(description="Manager category, for example billing_error."),
        origin: str = Field(description="customer, branch, or internal."),
        branch: str = Field(description="Branch slug, for example houston_med_center or central."),
        status: str = Field(default="open", description="open or in_progress for new tickets."),
    ) -> dict[str, Any]:
        if (block := denied("incident_create")) is not None:
            return block
        problems = _incident_fields(title, description, category, origin, branch, status)
        if problems:
            return finish("incident_create", ToolResult(ok=False, code=VALIDATION_ERROR, message=problems))
        payload = {
            "title": title.strip(),
            "description": description.strip(),
            "category": category.strip().lower(),
            "origin": origin.strip().lower(),
            "branch": branch.strip().lower(),
            "status": status.strip().lower(),
        }
        return finish("incident_create", _incident_call(api, "POST", "/api/incidents", json=payload))

    @mcp.tool(name="incident_update_status", description=UPDATE_DESCRIPTION)
    def incident_update_status(
        incident_id: str = Field(description="Incident id returned by the manager."),
        status: str = Field(description="New lifecycle status."),
    ) -> dict[str, Any]:
        if (block := denied("incident_update_status")) is not None:
            return block
        if len(incident_id.strip()) < 8:
            return finish(
                "incident_update_status",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="incident_id is required."),
            )
        if status.strip().lower() not in STATUSES:
            return finish(
                "incident_update_status",
                ToolResult(
                    ok=False,
                    code=VALIDATION_ERROR,
                    message="status must be open, in_progress, resolved, or discarded.",
                ),
            )
        path = f"/api/incidents/{incident_id.strip()}/status"
        return finish(
            "incident_update_status",
            _incident_call(api, "PATCH", path, json={"status": status.strip().lower()}),
        )

    @mcp.tool(name="incident_check_status", description=CHECK_DESCRIPTION)
    def incident_check_status(
        ticket_id: str | None = Field(default=None, description="One incident id."),
        status: str | None = Field(default=None, description="Filter: open, in_progress, resolved, or discarded."),
        category: str | None = Field(default=None, description="Filter: manager category slug."),
        origin: str | None = Field(default=None, description="Filter: customer, branch, or internal."),
        branch: str | None = Field(default=None, description="Filter: branch slug."),
        limit: int = Field(default=10, description="How many rows to return when listing. 1 to 50."),
    ) -> dict[str, Any]:
        if (block := denied("incident_check_status")) is not None:
            return block
        if ticket_id:
            if len(ticket_id.strip()) < 8:
                return finish(
                    "incident_check_status",
                    ToolResult(ok=False, code=VALIDATION_ERROR, message="ticket_id is required."),
                )
            path = f"/api/incidents/{ticket_id.strip()}"
            return finish("incident_check_status", _incident_call(api, "GET", path))
        if not any((status, category, origin, branch)):
            return finish(
                "incident_check_status",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="Provide a ticket_id or at least one filter."),
            )
        if status and status.strip().lower() not in STATUSES:
            return finish(
                "incident_check_status",
                ToolResult(
                    ok=False,
                    code=VALIDATION_ERROR,
                    message="status must be open, in_progress, resolved, or discarded.",
                ),
            )
        if category and category.strip().lower() not in CATEGORIES:
            return finish(
                "incident_check_status",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="category is not a valid manager category."),
            )
        if origin and origin.strip().lower() not in ORIGINS:
            return finish(
                "incident_check_status",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="origin must be customer, branch, or internal."),
            )
        if branch and branch.strip().lower() not in BRANCHES:
            return finish(
                "incident_check_status",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="branch is not a valid HealthCore branch."),
            )
        if not 1 <= limit <= 50:
            return finish(
                "incident_check_status",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="limit must be from 1 to 50."),
            )
        params = {
            key: value
            for key, value in (
                ("status", status.strip().lower() if status else None),
                ("category", category.strip().lower() if category else None),
                ("origin", origin.strip().lower() if origin else None),
                ("branch", branch.strip().lower() if branch else None),
                ("limit", limit),
            )
            if value is not None
        }
        return finish("incident_check_status", _incident_call(api, "GET", "/api/incidents", params=params))

    @mcp.tool(name="inventory_query", description=INVENTORY_DESCRIPTION)
    def inventory_query(
        operation: Literal["query", "create", "update", "delete", "adjust_stock"] = Field(
            default="query",
            description="Only query is performed. create, update, delete, and adjust_stock are rejected.",
        ),
        product_query: str | None = Field(
            default=None, description="Product name or SKU. Required when operation is query."
        ),
        quantity: int | None = Field(default=None, description="Ignored. Any write quantity is rejected."),
        stock: int | None = Field(default=None, description="Ignored. Setting stock is rejected."),
    ) -> dict[str, Any]:
        if (block := denied("inventory_query")) is not None:
            return block
        if operation != "query" or quantity is not None or stock is not None:
            return finish(
                "inventory_query",
                ToolResult(
                    ok=False,
                    code=INVENTORY_WRITE_FORBIDDEN,
                    message=(
                        "Inventory tools are read-only. Write operations are rejected and no stock was changed. "
                        "There is no inventory:write scope."
                    ),
                ),
            )
        if not product_query or len(product_query.strip()) < 2:
            return finish(
                "inventory_query",
                ToolResult(ok=False, code=VALIDATION_ERROR, message="product_query must be at least 2 characters."),
            )
        try:
            status_code, body = api.request("GET", "/inventory/products")
        except UpstreamError as exc:
            return finish("inventory_query", ToolResult(ok=False, code=UPSTREAM_ERROR, message=exc.message))
        if status_code != 200 or not isinstance(body, list):
            return finish(
                "inventory_query",
                ToolResult(ok=False, code=UPSTREAM_ERROR, message="The inventory manager did not return a product list."),
            )
        products = [_product(row) for row in body if _matches(product_query, str(row.get("name", "")), str(row.get("sku", "")))]
        if not products:
            return finish(
                "inventory_query",
                ToolResult(ok=True, code=OK, message="No product matched that query.", products=[], total=0),
            )
        shown = products[:5]
        return finish(
            "inventory_query",
            ToolResult(ok=True, code=OK, message=f"{len(products)} product(s) matched.", products=shown, total=len(products)),
        )


def _incident_fields(
    title: str,
    description: str,
    category: str,
    origin: str,
    branch: str,
    status: str,
) -> str:
    if not title.strip():
        return "title is required."
    if not description.strip():
        return "description is required."
    if category.strip().lower() not in CATEGORIES:
        return "category is not a valid manager category."
    if origin.strip().lower() not in ORIGINS:
        return "origin must be customer, branch, or internal."
    if branch.strip().lower() not in BRANCHES:
        return "branch is not a valid HealthCore branch."
    if status.strip().lower() not in {"open", "in_progress"}:
        return "status must be open or in_progress for new tickets."
    return ""


def _incident_call(api: HealthCoreApi, method: str, path: str, *, json: dict | None = None, params: dict | None = None) -> ToolResult:
    try:
        status_code, body = api.request(method, path, json=json, params=params)
    except UpstreamError as exc:
        return ToolResult(ok=False, code=UPSTREAM_ERROR, message=exc.message)
    if status_code == 404:
        return ToolResult(ok=False, code=INCIDENT_NOT_FOUND, message="Incident not found.")
    if status_code == 409:
        return ToolResult(ok=False, code=INCIDENT_CONFLICT, message="An incident with this ID already exists.")
    if status_code in (400, 422):
        return ToolResult(ok=False, code=VALIDATION_ERROR, message=_safe_detail(body))
    if status_code >= 400:
        return ToolResult(ok=False, code=UPSTREAM_ERROR, message="The incident manager rejected the call.")
    if isinstance(body, dict) and "items" in body:
        items = [_public_incident(item) for item in body.get("items") or [] if isinstance(item, dict)]
        total = int(body.get("total") or len(items))
        return ToolResult(ok=True, code=OK, message=f"{total} incident(s).", incidents=items, total=total)
    if isinstance(body, dict):
        return ToolResult(ok=True, code=OK, message="Incident loaded.", incident=_public_incident(body))
    return ToolResult(ok=False, code=UPSTREAM_ERROR, message="The incident manager returned a response that could not be read.")


def _public_incident(body: dict[str, Any]) -> dict[str, Any]:
    return {key: body.get(key) for key in INCIDENT_FIELDS}


def _safe_detail(body: object) -> str:
    if isinstance(body, dict) and isinstance(body.get("detail"), str) and "patient" not in body["detail"].lower():
        return body["detail"]
    return "The incident manager rejected these fields."


def _product(row: dict[str, Any]) -> dict[str, Any]:
    stock = int(row["current_stock"])
    threshold = int(row["threshold"])
    return {
        "name": row.get("name"),
        "sku": row.get("sku"),
        "category": row.get("category") or "",
        "current_stock": stock,
        "threshold": threshold,
        "below_threshold": stock < threshold,
    }


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_IGNORED = frozenset("a an any the of for in on box boxes pack packs some stock supply supplies".split())


def _stem(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") and not token.endswith("ss") else token


def _tokens(text: str) -> set[str]:
    return {_stem(token) for token in _TOKEN_RE.findall(text.lower()) if token not in _IGNORED}


def _matches(product_query: str, name: str, sku: str) -> bool:
    if product_query.strip().lower() == sku.lower():
        return True
    wanted = _tokens(product_query)
    return bool(wanted) and wanted <= _tokens(name)
