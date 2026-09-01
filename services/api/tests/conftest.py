"""Shared pytest fixtures. Each test gets an isolated TinyDB — never the live data files."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Must be set before Settings() is constructed.
os.environ["JWT_SECRET_KEY"] = "unit-test-jwt-secret-do-not-use-live"
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("RESET_TOKEN_EXPIRE_MINUTES", "30")

from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.result_store import store as incident_result_store  # noqa: E402
from app.stores import auth_store  # noqa: E402
from app import suppliers_store  # noqa: E402

TEST_JWT_SECRET = "unit-test-jwt-secret-do-not-use-live"
STAFF_EMAIL = "qa.staff@healthcore.example"
STAFF_PASSWORD = "StaffPass9"


@pytest.fixture(autouse=True)
def _isolate_persistence(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    suppliers_dir = tmp_path / "suppliers"
    suppliers_dir.mkdir()

    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setattr(auth_store, "DATA_DIR", auth_dir)
    monkeypatch.setattr(auth_store, "DB_PATH", auth_dir / "auth.json")
    monkeypatch.setattr(suppliers_store, "DATA_DIR", suppliers_dir)
    monkeypatch.setattr(suppliers_store, "DB_PATH", suppliers_dir / "suppliers.json")

    get_settings.cache_clear()
    incident_result_store._summary = None
    incident_result_store._csv = None
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    response = client.post(
        "/users",
        json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD,
            "name": "QA Staff",
            "phone": "",
            "address": "",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def auth_headers(client: TestClient, registered_user: dict) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
