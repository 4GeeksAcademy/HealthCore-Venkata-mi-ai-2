"""HTTP calls from the MCP server to the HealthCore API.

The server holds the service-account password. MCP clients never see it.
Incident status updates use ``PATCH /api/incidents/{id}/status`` only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

DEFAULT_API_URL = "http://127.0.0.1:8001"
TIMEOUT_SECONDS = 4.0


class UpstreamError(Exception):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


@dataclass
class ServiceAccount:
    base_url: str
    email: str
    password: str

    @classmethod
    def from_env(cls) -> ServiceAccount | None:
        email = os.getenv("AGENT_SERVICE_EMAIL")
        password = os.getenv("AGENT_SERVICE_PASSWORD")
        if not email or not password:
            return None
        base = os.getenv("HEALTHCORE_API_URL", DEFAULT_API_URL).rstrip("/")
        return cls(base, email, password)


class HealthCoreApi:
    """One login, one refresh on 401, a 4 second timeout. No patient_id in errors."""

    def __init__(self, account: ServiceAccount | None, client: httpx.Client | None = None) -> None:
        self.account = account
        self._owns_client = client is None
        if account is None:
            self._client = client
        else:
            self._client = client or httpx.Client(base_url=account.base_url, timeout=TIMEOUT_SECONDS)
        self._token: str | None = None

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()

    def request(self, method: str, path: str, *, json: dict | None = None, params: dict | None = None) -> tuple[int, object]:
        if self.account is None or self._client is None:
            raise UpstreamError("The MCP server is not configured with HealthCore API credentials.")
        try:
            response = self._send(method, path, json=json, params=params)
            if response.status_code == 401:
                self._token = None
                response = self._send(method, path, json=json, params=params)
        except httpx.TimeoutException as exc:
            raise UpstreamError("The company API did not respond in time.") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("The company API is not reachable.") from exc
        return response.status_code, _json_or_text(response)

    def _send(self, method: str, path: str, *, json: dict | None, params: dict | None) -> httpx.Response:
        if self._token is None:
            self._login()
        assert self._client is not None
        return self._client.request(
            method,
            path,
            json=json,
            params=params,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=TIMEOUT_SECONDS,
        )

    def _login(self) -> None:
        assert self.account is not None and self._client is not None
        try:
            response = self._client.post(
                "/auth/login",
                json={"email": self.account.email, "password": self.account.password},
                timeout=TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException as exc:
            raise UpstreamError("The company API did not respond in time.") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("The company API is not reachable.") from exc
        if response.status_code != 200:
            raise UpstreamError("The MCP server could not sign in to the company API.", status=response.status_code)
        body = response.json()
        token = body.get("access_token") if isinstance(body, dict) else None
        if not isinstance(token, str) or not token:
            raise UpstreamError("The company API sign-in response had no access token.")
        self._token = token


def _json_or_text(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return {"detail": "The company API returned a response that was not JSON."}
