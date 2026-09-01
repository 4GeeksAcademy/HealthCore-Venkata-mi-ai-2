"""POST /auth/forgot-password — no email enumeration; hashed reset secrets."""

from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient
from tinydb import TinyDB

from app.stores import auth_store
from tests.conftest import STAFF_EMAIL

GENERIC_MESSAGE = "If that address is registered, you'll receive a link shortly."
KNOWN_RAW_TOKEN = "unit-test-reset-token-value-32b"


def test_forgot_password_stores_hashed_token_for_registered_email(
    client: TestClient, registered_user: dict, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.routers.auth.secrets.token_urlsafe", lambda _nbytes: KNOWN_RAW_TOKEN
    )

    response = client.post("/auth/forgot-password", json={"email": STAFF_EMAIL})

    assert response.status_code == 200
    assert response.json()["message"] == GENERIC_MESSAGE

    db = TinyDB(auth_store.DB_PATH)
    try:
        rows = db.table(auth_store.RESET_TOKENS_TABLE).all()
    finally:
        db.close()

    expected_hash = hashlib.sha256(KNOWN_RAW_TOKEN.encode("utf-8")).hexdigest()
    assert any(row["token_hash"] == expected_hash for row in rows)
    assert all(row["token_hash"] != KNOWN_RAW_TOKEN for row in rows)
    assert KNOWN_RAW_TOKEN not in response.text


def test_forgot_password_same_message_for_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/auth/forgot-password", json={"email": "nobody@healthcore.example"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == GENERIC_MESSAGE

    db = TinyDB(auth_store.DB_PATH)
    try:
        rows = db.table(auth_store.RESET_TOKENS_TABLE).all()
    finally:
        db.close()
    assert rows == []


def test_forgot_password_rejects_malformed_email(client: TestClient) -> None:
    response = client.post("/auth/forgot-password", json={"email": "not-an-email"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid request. Please check the submitted data."
