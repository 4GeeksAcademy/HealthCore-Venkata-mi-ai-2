"""Read-only, time-bounded HTTP session to the HealthCore API, shared by the tools.

Credentials come from the environment only (service account, the same bearer
flow as ``services/api/profile_cache.py``). The only non-GET request this
session can send is ``POST /auth/login`` to obtain that token.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx

TOOL_TIMEOUT_SECONDS = 4.0
LOGIN_PATH = "/auth/login"
DEFAULT_API_URL = "http://localhost:8001"


class ReadOnlyViolation(RuntimeError):
    """A tool tried to send a request that could change data."""


class ToolCallError(Exception):
    """Expected failure, mapped by the tool to a ``ToolStatus``."""

    def __init__(self, status: str, http_status: int | None = None) -> None:
        super().__init__(status)
        self.status = status
        self.http_status = http_status


@dataclass(frozen=True)
class ServiceCredentials:
    base_url: str
    email: str
    password: str

    @classmethod
    def from_env(cls) -> ServiceCredentials | None:
        email = os.getenv("AGENT_SERVICE_EMAIL", "").strip()
        password = os.getenv("AGENT_SERVICE_PASSWORD", "")
        if not email or not password:
            return None
        base_url = os.getenv("HEALTHCORE_API_URL", "").strip() or DEFAULT_API_URL
        return cls(base_url=base_url.rstrip("/"), email=email, password=password)


class ReadOnlyApiSession:
    def __init__(
        self,
        credentials: ServiceCredentials,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = TOOL_TIMEOUT_SECONDS,
    ) -> None:
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self._client = client or httpx.Client(base_url=credentials.base_url)
        self._token: str | None = None
        self._token_lock = threading.Lock()

    def close(self) -> None:
        self._client.close()

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> tuple[Any, int]:
        """GET ``path`` within one ``timeout_seconds`` budget, login included."""
        deadline = time.monotonic() + self.timeout_seconds
        response = self._authorized_get(path, params, deadline)
        if response.status_code == 401:
            with self._token_lock:
                self._token = None
            response = self._authorized_get(path, params, deadline)
        if response.status_code in (401, 403):
            raise ToolCallError("auth_failed", response.status_code)
        if response.status_code == 404:
            raise ToolCallError("not_found", 404)
        if response.status_code >= 400:
            raise ToolCallError("unavailable", response.status_code)
        try:
            return response.json(), response.status_code
        except ValueError as exc:
            raise ToolCallError("bad_response", response.status_code) from exc

    def _authorized_get(self, path: str, params: dict[str, Any] | None, deadline: float) -> httpx.Response:
        token = self._bearer(deadline)
        return self._send("GET", path, deadline, params=params, headers={"Authorization": f"Bearer {token}"})

    def _bearer(self, deadline: float) -> str:
        with self._token_lock:
            if self._token:
                return self._token
            response = self._send(
                "POST",
                LOGIN_PATH,
                deadline,
                json={"email": self.credentials.email, "password": self.credentials.password},
            )
            if response.status_code in (400, 401, 403, 422):
                raise ToolCallError("auth_failed", response.status_code)
            if response.status_code >= 400:
                raise ToolCallError("unavailable", response.status_code)
            try:
                self._token = str(response.json()["access_token"])
            except (ValueError, KeyError, TypeError) as exc:
                raise ToolCallError("bad_response", response.status_code) from exc
            return self._token

    def _send(self, method: str, path: str, deadline: float, **kwargs: Any) -> httpx.Response:
        if method != "GET" and not (method == "POST" and path == LOGIN_PATH):
            raise ReadOnlyViolation(f"{method} {path} is not allowed from an agent tool")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ToolCallError("timeout")
        try:
            return self._client.request(method, path, timeout=remaining, **kwargs)
        except httpx.TimeoutException as exc:
            raise ToolCallError("timeout") from exc
        except httpx.TransportError as exc:
            raise ToolCallError("unavailable") from exc
