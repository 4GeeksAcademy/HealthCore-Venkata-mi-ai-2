"""Streamable HTTP MCP server. OAuth is MCP Auth, not FastMCP's auth helpers.

The MCP Python SDK's ``FastMCP`` is constructed with ``auth=None``. Bearer
checks, Protected Resource Metadata, and scopes come from ``mcpauth``.
"""

from __future__ import annotations

import logging
import os

import anyio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from urllib.parse import urlparse

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcpauth import MCPAuth
from mcpauth.config import AuthServerConfig, AuthServerType, AuthorizationServerMetadata
from mcpauth.types import ResourceServerConfig, ResourceServerMetadata
from mcpauth.utils import validate_server_config
from mcpauth.exceptions import (
    BearerAuthExceptionCode,
    MCPAuthBearerAuthException,
    MCPAuthBearerAuthExceptionDetails,
)
from mcpauth.middleware.create_bearer_auth import _handle_error, get_bearer_token_from_headers
from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .backend import HealthCoreApi, ServiceAccount
from .errors import AUTHORIZATION_CODE, EXIT_AUTH_CONFIG, EXIT_BIND_FAILED, EXIT_OK, EXIT_STARTUP_VALIDATION
from .oauth import SCOPES, AuthorizationService, OAuthClient
from .tools import TOOL_SCOPES, audit_log, register_tools

logger = logging.getLogger(__name__)

# A path ending in "/mcp" is rewritten by a local HTTP filter on this workstation:
# Content-Length is removed and Transfer-Encoding: chunked is advertised without
# chunk framing, so clients hang. The resource path must not end in "/mcp".
STREAM_PATH = "/healthcore-tools"

INSTRUCTIONS = (
    "HealthCore Digital tools. incident_create and incident_update_status need scope "
    "incidents:write. incident_update_status calls PATCH /api/incidents/{id}/status only. "
    "incident_check_status needs incidents:read. inventory_query needs inventory:read and "
    "rejects every write with inventory_write_forbidden. A client without a valid access "
    "token cannot list or call tools."
)


class ConfigError(Exception):
    """The process should exit 1. The message is safe to print."""


@dataclass
class Settings:
    public_url: str
    host: str = "127.0.0.1"
    port: int = 8010
    clients: dict[str, OAuthClient] = field(default_factory=dict)
    account: ServiceAccount | None = None

    @property
    def issuer(self) -> str:
        return self.public_url.rstrip("/")

    @property
    def resource_id(self) -> str:
        return f"{self.issuer}{STREAM_PATH}"

    @classmethod
    def from_env(cls) -> Settings:
        public = os.getenv("MCP_PUBLIC_URL", "http://127.0.0.1:8010").rstrip("/")
        parsed = urlparse(public)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigError("MCP_PUBLIC_URL must be an http or https URL with a host.")
        port = int(os.getenv("MCP_PORT") or parsed.port or (443 if parsed.scheme == "https" else 8010))
        host = os.getenv("MCP_BIND_HOST", "127.0.0.1")
        clients: dict[str, OAuthClient] = {}
        agent_id = os.getenv("MCP_AGENT_CLIENT_ID")
        agent_secret = os.getenv("MCP_AGENT_CLIENT_SECRET")
        if agent_id and agent_secret:
            clients[agent_id] = OAuthClient(agent_id, agent_secret, frozenset({"incidents:read"}))
        ops_id = os.getenv("MCP_OPS_CLIENT_ID")
        ops_secret = os.getenv("MCP_OPS_CLIENT_SECRET")
        if ops_id and ops_secret:
            clients[ops_id] = OAuthClient(ops_id, ops_secret, frozenset(SCOPES))
        return cls(public_url=public, host=host, port=port, clients=clients, account=ServiceAccount.from_env())


def create_app(settings: Settings, api: HealthCoreApi | None = None) -> Starlette:
    parsed = urlparse(settings.issuer)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError("MCP_PUBLIC_URL must be an http or https URL with a host.")
    authz = AuthorizationService(issuer=settings.issuer, resource_id=settings.resource_id, clients=dict(settings.clients))
    auth_server = AuthServerConfig(
        type=AuthServerType.OIDC,
        metadata=AuthorizationServerMetadata(
            issuer=settings.issuer,
            authorization_endpoint=f"{settings.issuer}/oauth/authorize",
            token_endpoint=f"{settings.issuer}/oauth/token",
            jwks_uri=f"{settings.issuer}/.well-known/jwks.json",
            registration_endpoint=f"{settings.issuer}/oauth/register",
            scopes_supported=list(SCOPES),
            response_types_supported=["code"],
            grant_types_supported=["authorization_code", "client_credentials"],
            code_challenge_methods_supported=["S256"],
            token_endpoint_auth_methods_supported=["client_secret_post", "client_secret_basic", "none"],
        ),
    )
    validation = validate_server_config(auth_server)
    if not validation.is_valid:
        raise ValueError("startup_validation: " + "; ".join(error.code for error in validation.errors))

    mcp_auth = MCPAuth(
        protected_resources=[
            ResourceServerConfig(
                metadata=ResourceServerMetadata(
                    resource=settings.resource_id,
                    authorization_servers=[auth_server],
                    scopes_supported=list(SCOPES),
                    bearer_methods_supported=["header"],
                    resource_name="HealthCore company tools",
                )
            )
        ]
    )
    api = api if api is not None else HealthCoreApi(settings.account)
    netloc = parsed.netloc
    mcp = FastMCP(
        name="HealthCore company tools",
        instructions=INSTRUCTIONS,
        auth=None,
        host=settings.host,
        port=settings.port,
        streamable_http_path=STREAM_PATH,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[netloc, f"{settings.host}:*", "127.0.0.1:*", "localhost:*"],
            allowed_origins=[settings.issuer, f"http://{settings.host}:{settings.port}", f"http://127.0.0.1:{settings.port}"],
        ),
    )
    register_tools(mcp, api, lambda: mcp_auth.auth_info)
    mcp_http = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        async with mcp_http.router.lifespan_context(mcp_http):
            yield
        api.close()

    return Starlette(
        lifespan=lifespan,
        middleware=[Middleware(_cors)],
        routes=[
            Route("/.well-known/openid-configuration", endpoint=lambda request: JSONResponse(authz.metadata()), methods=["GET"]),
            Route("/.well-known/oauth-authorization-server", endpoint=lambda request: JSONResponse(authz.metadata()), methods=["GET"]),
            Route("/.well-known/jwks.json", endpoint=lambda request: JSONResponse({"keys": [authz.public_jwk]}), methods=["GET"]),
            Route("/oauth/register", endpoint=authz.register, methods=["POST"]),
            Route("/oauth/authorize", endpoint=authz.authorize, methods=["GET", "POST"]),
            Route("/oauth/token", endpoint=authz.token, methods=["POST"]),
            *mcp_auth.resource_metadata_router().routes,
            Mount(
                "/",
                app=mcp_http,
                middleware=[
                    Middleware(
                        _bearer_gate(
                            mcp_auth,
                            authz.verify_access_token,
                            issuer=settings.issuer,
                            audience=settings.resource_id,
                            resource=settings.resource_id,
                        )
                    ),
                    Middleware(_scope_gate(mcp_auth)),
                ],
            ),
        ],
    )


class _cors:
    """Allow a browser MCP client to call this server. Adds headers only; does not buffer the body."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_cors(message) -> None:
            if message["type"] == "http.response.start":
                headers = [tuple(item) for item in (message.get("headers") or [])]
                if not any(name.lower() == b"access-control-allow-origin" for name, _value in headers):
                    headers.append((b"access-control-allow-origin", b"*"))
                message = {**message, "headers": headers}
            await send(message)

        if scope.get("method") == "OPTIONS":
            await send_with_cors(
                {
                    "type": "http.response.start",
                    "status": 204,
                    "headers": [
                        (b"access-control-allow-methods", b"GET, POST, OPTIONS"),
                        (b"access-control-allow-headers", b"*"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b""})
            return
        await self.app(scope, receive, send_with_cors)


def _bearer_gate(mcp_auth: MCPAuth, verify, *, issuer: str, audience: str, resource: str) -> type:
    """Check the bearer token without buffering the body.

    MCP Auth's middleware is Starlette BaseHTTPMiddleware, which holds a streaming
    response until the app finishes. Streamable HTTP never finishes that stream,
    so the client handshake stalls. This gate only reads the Authorization header.
    """

    class BearerGate:
        def __init__(self, app) -> None:
            self.app = app

        async def __call__(self, scope, receive, send) -> None:
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return
            try:
                token = get_bearer_token_from_headers(Headers(scope=scope))
                auth_info = verify(token)
                if auth_info.issuer != issuer:
                    raise MCPAuthBearerAuthException(
                        BearerAuthExceptionCode.INVALID_ISSUER,
                        cause=MCPAuthBearerAuthExceptionDetails(expected=issuer, actual=auth_info.issuer),
                    )
                audiences = auth_info.audience if isinstance(auth_info.audience, list) else [auth_info.audience]
                if audience not in audiences:
                    raise MCPAuthBearerAuthException(
                        BearerAuthExceptionCode.INVALID_AUDIENCE,
                        cause=MCPAuthBearerAuthExceptionDetails(expected=audience, actual=auth_info.audience),
                    )
            except Exception as error:
                status, body, extra = _handle_error(error, resource, False)
                await _send_json(send, status, body, extra)
                return
            context = mcp_auth._context_var.set(auth_info)
            try:
                await self.app(scope, receive, send)
            finally:
                mcp_auth._context_var.reset(context)

    return BearerGate


async def _send_json(send, status: int, body: dict, extra_headers: dict) -> None:
    import json

    encoded = json.dumps(body).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(encoded)).encode("ascii")),
    ]
    for name, value in extra_headers.items():
        headers.append((name.lower().encode("latin-1"), str(value).encode("latin-1")))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": encoded})


def _scope_gate(mcp_auth: MCPAuth) -> type:
    """Reject a tools/call whose token lacks the tool scope. Replays the body for the MCP app."""

    class ToolScopeMiddleware:
        def __init__(self, app) -> None:
            self.app = app

        async def __call__(self, scope, receive, send) -> None:
            if scope["type"] != "http" or scope.get("method") != "POST":
                await self.app(scope, receive, send)
                return
            body = await _read_body(receive)
            denial = _scope_denial(body, mcp_auth)
            if denial is not None:
                await denial(send)
                return
            delivered = False

            async def replay():
                nonlocal delivered
                if delivered:
                    # A second receive means the response is checking for a client
                    # disconnect. Reporting one aborts a larger JSON body.
                    await anyio.sleep_forever()
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}

            await self.app(scope, replay, send)

    return ToolScopeMiddleware


def _scope_denial(body: bytes, mcp_auth: MCPAuth):
    import json

    try:
        payload = json.loads(body)
    except (UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("method") != "tools/call":
        return None
    name = str((payload.get("params") or {}).get("name") or "")
    needed = TOOL_SCOPES.get(name)
    if not needed:
        return None
    info = mcp_auth.auth_info
    held = set(getattr(info, "scopes", None) or [])
    missing = [scope for scope in needed if scope not in held]
    if not missing:
        return None
    # MCP Auth's required_scopes is one list for every request. A read-only
    # client must still be able to list tools, so each tool applies that same
    # check and the same 403 body.
    error = MCPAuthBearerAuthException(
        BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES,
        cause=MCPAuthBearerAuthExceptionDetails(missing_scopes=missing),
    )
    status, body, extra = _handle_error(error, None, False)
    audit_log.info(
        "tool=%s client=%s subject=%s result=%s",
        name,
        (getattr(info, "client_id", None) or "unknown"),
        (getattr(info, "subject", None) or "unknown"),
        body.get("error", AUTHORIZATION_CODE),
    )
    encoded = json.dumps(body).encode("utf-8")

    async def send_denial(send) -> None:
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(encoded)).encode("ascii")),
        ]
        for header_name, header_value in extra.items():
            headers.append((header_name.lower().encode("latin-1"), str(header_value).encode("latin-1")))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": encoded})

    return send_denial


async def _read_body(receive) -> bytes:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        chunks.append(message.get("body") or b"")
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    try:
        settings = Settings.from_env()
        app = create_app(settings)
    except ConfigError as exc:
        print(f"auth_config: {exc}", flush=True)
        return EXIT_AUTH_CONFIG
    except ValueError as exc:
        print(f"startup_validation: {exc}", flush=True)
        return EXIT_STARTUP_VALIDATION
    if not _port_is_free(settings.host, settings.port):
        print(f"bind_failed: {settings.host}:{settings.port} is already in use", flush=True)
        return EXIT_BIND_FAILED
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
    return EXIT_OK


def _port_is_free(host: str, port: int) -> bool:
    import socket

    sock = socket.socket()
    try:
        sock.bind((host, port))
    except OSError:
        return False
    finally:
        sock.close()
    return True
