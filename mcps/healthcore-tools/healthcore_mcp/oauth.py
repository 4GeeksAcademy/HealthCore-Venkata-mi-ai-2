"""In-process OAuth 2.1 / OIDC authorization server for the MCP resource server.

HealthCore staff JWTs are HS256 tokens from ``POST /auth/login``. They are not
an OIDC provider, so MCP Auth cannot validate them. This issuer publishes
discovery metadata, a JWKS, authorization-code + PKCE (S256), client credentials,
and dynamic client registration. Access tokens are RS256 JWTs whose audience is
the MCP resource. MCP Auth checks those tokens; this module does not sit inside
FastMCP's auth layer.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass, field

import jwt
from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from .errors import EXIT_STARTUP_VALIDATION

SCOPES = ("incidents:read", "incidents:write", "inventory:read")
TOKEN_TTL_SECONDS = 3600
CODE_TTL_SECONDS = 120


class OAuthError(Exception):
    def __init__(self, error: str, description: str, status: int) -> None:
        super().__init__(description)
        self.error = error
        self.description = description
        self.status = status


@dataclass
class OAuthClient:
    client_id: str
    client_secret: str | None
    scopes: frozenset[str]
    redirect_uris: tuple[str, ...] = ()
    token_endpoint_auth_method: str = "client_secret_post"


@dataclass
class AuthorizationService:
    issuer: str
    resource_id: str
    clients: dict[str, OAuthClient] = field(default_factory=dict)
    _private_key: rsa.RSAPrivateKey = field(default_factory=lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048))
    _codes: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = [scope for client in self.clients.values() for scope in client.scopes if scope not in SCOPES]
        if unknown:
            raise ValueError(f"startup_validation: unknown scope(s) {sorted(set(unknown))}")

    @property
    def public_jwk(self) -> dict:
        jwk = json_jwk(self._private_key.public_key())
        jwk.update({"kid": "healthcore-mcp-1", "use": "sig", "alg": "RS256"})
        return jwk

    def metadata(self) -> dict:
        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{self.issuer}/oauth/authorize",
            "token_endpoint": f"{self.issuer}/oauth/token",
            "jwks_uri": f"{self.issuer}/.well-known/jwks.json",
            "registration_endpoint": f"{self.issuer}/oauth/register",
            "scopes_supported": list(SCOPES),
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "client_credentials"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        }

    def issue_token(self, *, client: OAuthClient, scopes: list[str], subject: str) -> str:
        now = int(time.time())
        payload = {
            "iss": self.issuer,
            "sub": subject,
            "aud": self.resource_id,
            "client_id": client.client_id,
            "scope": " ".join(scopes),
            "iat": now,
            "exp": now + TOKEN_TTL_SECONDS,
        }
        return jwt.encode(payload, self._private_key, algorithm="RS256", headers={"kid": "healthcore-mcp-1"})

    def verify_access_token(self, token: str):
        """Signature and issuer only. MCP Auth checks audience and scopes."""
        from mcpauth.exceptions import (
            MCPAuthTokenVerificationException,
            MCPAuthTokenVerificationExceptionCode,
        )
        from mcpauth.types import AuthInfo

        try:
            claims = jwt.decode(
                token,
                self._private_key.public_key(),
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise MCPAuthTokenVerificationException(
                MCPAuthTokenVerificationExceptionCode.INVALID_TOKEN
            ) from exc
        scope = claims.get("scope", "")
        scopes = scope.split() if isinstance(scope, str) else list(scope)
        audience = claims.get("aud")
        return AuthInfo(
            token=token,
            issuer=str(claims["iss"]),
            subject=str(claims["sub"]),
            client_id=claims.get("client_id"),
            scopes=scopes,
            audience=audience,
            claims=claims,
        )

    def _client_or_401(self, client_id: str, client_secret: str | None, *, public_ok: bool) -> OAuthClient:
        client = self.clients.get(client_id)
        if client is None:
            raise OAuthError("invalid_client", "Unknown client_id.", 401)
        if client.client_secret is None:
            if not public_ok:
                raise OAuthError("invalid_client", "This client must use authorization code with PKCE.", 401)
            return client
        if client.client_secret != client_secret:
            raise OAuthError("invalid_client", "Client authentication failed.", 401)
        return client

    def _granted_scopes(self, client: OAuthClient, requested: str | None) -> list[str]:
        if not requested:
            return sorted(client.scopes)
        scopes = requested.split()
        if any(scope not in client.scopes for scope in scopes):
            raise OAuthError("invalid_scope", "The client is not allowed to request that scope.", 400)
        return scopes

    async def register(self, request: Request) -> Response:
        try:
            body = await request.json()
        except Exception:
            return _oauth_error("invalid_request", "Registration body must be JSON.", 400)
        if not isinstance(body, dict):
            return _oauth_error("invalid_request", "Registration body must be a JSON object.", 400)
        redirects = body.get("redirect_uris") or []
        if not isinstance(redirects, list) or not redirects or not all(isinstance(item, str) for item in redirects):
            return _oauth_error("invalid_request", "redirect_uris must be a non-empty list of URLs.", 400)
        requested = body.get("scope") or " ".join(SCOPES)
        scopes = [scope for scope in str(requested).split() if scope in SCOPES]
        if not scopes:
            return _oauth_error("invalid_scope", "No supported scope was requested.", 400)
        client_id = "dyn-" + secrets.token_urlsafe(12)
        method = str(body.get("token_endpoint_auth_method") or "none")
        secret = None if method == "none" else secrets.token_urlsafe(24)
        self.clients[client_id] = OAuthClient(
            client_id=client_id,
            client_secret=secret,
            scopes=frozenset(scopes),
            redirect_uris=tuple(redirects),
            token_endpoint_auth_method=method,
        )
        payload = {
            "client_id": client_id,
            "client_secret": secret,
            "redirect_uris": list(redirects),
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": method,
            "scope": " ".join(scopes),
        }
        if secret is None:
            payload.pop("client_secret")
        return JSONResponse(payload, status_code=201)

    async def authorize(self, request: Request) -> Response:
        params = request.query_params
        if request.method == "POST":
            form = await request.form()
            params = form
        client_id = str(params.get("client_id") or "")
        redirect_uri = str(params.get("redirect_uri") or "")
        state = str(params.get("state") or "")
        challenge = str(params.get("code_challenge") or "")
        method = str(params.get("code_challenge_method") or "")
        scope = str(params.get("scope") or "")
        response_type = str(params.get("response_type") or "")
        client = self.clients.get(client_id)
        if client is None or redirect_uri not in client.redirect_uris:
            return _oauth_error("invalid_request", "Unknown client or redirect_uri is not registered.", 400)
        if response_type != "code" or method != "S256" or not challenge:
            return _oauth_error("invalid_request", "response_type must be code and PKCE S256 is required.", 400)
        try:
            scopes = self._granted_scopes(client, scope or None)
        except OAuthError as exc:
            return _oauth_error(exc.error, exc.description, exc.status)
        if request.method == "GET":
            scope_text = " ".join(scopes)
            return HTMLResponse(
                "<!doctype html><html><head><title>HealthCore MCP authorization</title></head>"
                "<body><h1>HealthCore Digital</h1>"
                f"<p>Client <code>{_escape(client_id)}</code> is asking for: {_escape(scope_text)}</p>"
                "<form method='post'>"
                f"<input type='hidden' name='client_id' value='{_escape(client_id)}'/>"
                f"<input type='hidden' name='redirect_uri' value='{_escape(redirect_uri)}'/>"
                f"<input type='hidden' name='state' value='{_escape(state)}'/>"
                f"<input type='hidden' name='code_challenge' value='{_escape(challenge)}'/>"
                "<input type='hidden' name='code_challenge_method' value='S256'/>"
                "<input type='hidden' name='response_type' value='code'/>"
                f"<input type='hidden' name='scope' value='{_escape(scope_text)}'/>"
                "<button type='submit'>Approve</button></form></body></html>"
            )
        code = secrets.token_urlsafe(24)
        self._codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "challenge": challenge,
            "scopes": scopes,
            "exp": time.time() + CODE_TTL_SECONDS,
        }
        location = redirect_uri + ("&" if "?" in redirect_uri else "?") + "code=" + code
        if state:
            location += "&state=" + state
        return RedirectResponse(location, status_code=302)

    async def token(self, request: Request) -> Response:
        form = await request.form()
        client_id = str(form.get("client_id") or "")
        client_secret = form.get("client_secret")
        client_secret = None if client_secret is None else str(client_secret)
        header = request.headers.get("authorization") or ""
        if header.lower().startswith("basic "):
            try:
                decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
                basic_id, basic_secret = decoded.split(":", 1)
            except (ValueError, UnicodeError):
                return _oauth_error("invalid_client", "Basic client authentication could not be read.", 401)
            client_id = client_id or basic_id
            client_secret = client_secret if client_secret is not None else basic_secret
        grant = str(form.get("grant_type") or "")
        try:
            if grant == "client_credentials":
                client = self._client_or_401(client_id, client_secret, public_ok=False)
                scopes = self._granted_scopes(client, form.get("scope"))
                subject = client.client_id
            elif grant == "authorization_code":
                client = self._client_or_401(client_id, client_secret, public_ok=True)
                code = str(form.get("code") or "")
                verifier = str(form.get("code_verifier") or "")
                redirect_uri = str(form.get("redirect_uri") or "")
                stored = self._codes.pop(code, None)
                if stored is None or stored["exp"] < time.time():
                    raise OAuthError("invalid_grant", "Authorization code is unknown or expired.", 400)
                if stored["client_id"] != client.client_id or stored["redirect_uri"] != redirect_uri:
                    raise OAuthError("invalid_grant", "Authorization code does not match this client.", 400)
                if _s256(verifier) != stored["challenge"]:
                    raise OAuthError("invalid_grant", "PKCE verification failed.", 400)
                scopes = list(stored["scopes"])
                subject = client.client_id
            else:
                raise OAuthError("unsupported_grant_type", "Use authorization_code or client_credentials.", 400)
        except OAuthError as exc:
            return _oauth_error(exc.error, exc.description, exc.status)
        access = self.issue_token(client=client, scopes=scopes, subject=subject)
        return JSONResponse(
            {
                "access_token": access,
                "token_type": "Bearer",
                "expires_in": TOKEN_TTL_SECONDS,
                "scope": " ".join(scopes),
            }
        )


def json_jwk(public_key: rsa.RSAPublicKey) -> dict:
    return RSAAlgorithm.to_jwk(public_key, as_dict=True)


def _s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _oauth_error(error: str, description: str, status: int) -> JSONResponse:
    return JSONResponse({"error": error, "error_description": description}, status_code=status)


def startup_validation_exit() -> int:
    """Process exit when authorization-server metadata would not pass MCP Auth's checks."""
    return EXIT_STARTUP_VALIDATION
