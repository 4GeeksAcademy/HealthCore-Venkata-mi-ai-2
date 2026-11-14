"""Production ticket lookup. The incident manager is reached only through the MCP server.

``langchain_mcp_adapters`` loads ``incident_check_status`` from the server and
invokes it. This module does not call ``/api/incidents``.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from .contracts import TicketLookupInput, TicketLookupOutput, TicketRecord

TOOL_NAME = "ticket_lookup"
MCP_TOOL = "incident_check_status"
ENDPOINT = "mcp:incident_check_status"


def mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    """HTTP client for the MCP SDK.

    The protocol version header is sent. Set ``MCP_STRIP_PROTOCOL_HEADER=1`` only
    on a machine whose HTTP filter rewrites responses that carry
    ``mcp-protocol-version`` (it drops Content-Length and leaves a broken chunked
    body). The server accepts the call either way.
    """

    class _Passthrough(httpx.AsyncBaseTransport):
        def __init__(self) -> None:
            self._inner = httpx.AsyncHTTPTransport()

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if os.getenv("MCP_STRIP_PROTOCOL_HEADER") == "1":
                request.headers.pop("mcp-protocol-version", None)
            return await self._inner.handle_async_request(request)

    kwargs: dict[str, Any] = {
        "transport": _Passthrough(),
        "timeout": timeout or httpx.Timeout(30.0, read=300.0),
    }
    if headers is not None:
        kwargs["headers"] = headers
    if auth is not None:
        kwargs["auth"] = auth
    return httpx.AsyncClient(**kwargs)


@dataclass(frozen=True)
class McpIncidentLookup:
    mcp_url: str | None = None
    token_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    resource: str | None = None
    timeout_seconds: float = 4.0

    @classmethod
    def from_env(cls) -> McpIncidentLookup:
        return cls(
            mcp_url=os.getenv("HEALTHCORE_MCP_URL") or None,
            token_url=os.getenv("MCP_TOKEN_URL") or None,
            client_id=os.getenv("MCP_AGENT_CLIENT_ID") or None,
            client_secret=os.getenv("MCP_AGENT_CLIENT_SECRET") or None,
            resource=os.getenv("MCP_RESOURCE_ID") or None,
        )

    @property
    def configured(self) -> bool:
        return bool(self.mcp_url and self.token_url and self.client_id and self.client_secret)

    def __call__(self, request: TicketLookupInput) -> TicketLookupOutput:
        if not self.configured:
            return TicketLookupOutput(status="auth_failed", endpoint=ENDPOINT)
        try:
            raw = _run(asyncio.wait_for(self._invoke(request), timeout=self.timeout_seconds))
        except TimeoutError:
            return TicketLookupOutput(status="timeout", endpoint=ENDPOINT)
        except httpx.TimeoutException:
            return TicketLookupOutput(status="timeout", endpoint=ENDPOINT)
        except httpx.HTTPError:
            return TicketLookupOutput(status="unavailable", endpoint=ENDPOINT)
        except Exception as exc:
            text = str(exc).lower()
            if "401" in text or "invalid_token" in text or "missing_auth" in text:
                return TicketLookupOutput(status="auth_failed", endpoint=ENDPOINT)
            if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
                return TicketLookupOutput(status="timeout", endpoint=ENDPOINT)
            return TicketLookupOutput(status="unavailable", endpoint=ENDPOINT)
        return _to_output(raw)


    async def _invoke(self, request: TicketLookupInput) -> Any:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        token = await self._access_token()
        client = MultiServerMCPClient(
            {
                "healthcore": {
                    "transport": "streamable_http",
                    "url": self.mcp_url,
                    "headers": {"Authorization": f"Bearer {token}"},
                    "timeout": self.timeout_seconds,
                    "httpx_client_factory": mcp_http_client,
                }
            }
        )
        tools = await client.get_tools()
        tool = next((item for item in tools if item.name == MCP_TOOL), None)
        if tool is None:
            raise RuntimeError("incident_check_status was not in the MCP tool list")
        arguments: dict[str, Any] = {}
        if request.ticket_id:
            arguments["ticket_id"] = request.ticket_id
        else:
            if request.status:
                arguments["status"] = request.status
            if request.category:
                arguments["category"] = request.category
            if request.branch:
                arguments["branch"] = request.branch
            arguments["limit"] = request.limit
        return await tool.ainvoke(arguments)

    async def _access_token(self) -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "incidents:read",
        }
        if self.resource:
            data["resource"] = self.resource
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as http:
            response = await http.post(self.token_url, data=data)
        if response.status_code != 200:
            raise RuntimeError(f"token endpoint returned {response.status_code}")
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("token endpoint returned no access_token")
        return token


def _run(awaitable):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, awaitable).result()


def _to_output(raw: Any) -> TicketLookupOutput:
    try:
        body = _as_dict(raw)
        code = str(body.get("code") or "")
        if code == "ok":
            rows = body.get("incidents")
            if rows is None and isinstance(body.get("incident"), dict):
                rows = [body["incident"]]
            tickets = tuple(TicketRecord.model_validate(row) for row in rows or [])
            return TicketLookupOutput(
                status="ok",
                tickets=tickets,
                total=int(body.get("total") if body.get("total") is not None else len(tickets)),
                http_status=200,
                endpoint=ENDPOINT,
            )
        status = {
            "incident_not_found": "not_found",
            "validation_error": "invalid_input",
            "missing_required_scopes": "auth_failed",
            "invalid_token": "auth_failed",
            "upstream_error": "unavailable",
        }.get(code, "bad_response")
        return TicketLookupOutput(status=status, endpoint=ENDPOINT)
    except (TypeError, ValueError, KeyError):
        return TicketLookupOutput(status="bad_response", endpoint=ENDPOINT)


def _as_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    if isinstance(raw, list) and raw:
        first = raw[0]
        if isinstance(first, dict) and "text" in first:
            parsed = json.loads(first["text"])
            if isinstance(parsed, dict):
                return parsed
        if isinstance(first, str):
            parsed = json.loads(first)
            if isinstance(parsed, dict):
                return parsed
    raise TypeError("MCP tool result was not a JSON object")
