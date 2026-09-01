"""POST /auth/reset-password — one-time hashed tokens replace the password."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.stores import auth_store
from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD

KNOWN_RAW_TOKEN = "unit-test-reset-token-value-32b"
NEW_PASSWORD = "NewStaffPass9"


def test_reset_password_replaces_credentials(
    client: TestClient, registered_user: dict, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.routers.auth.secrets.token_urlsafe", lambda _nbytes: KNOWN_RAW_TOKEN
    )
    assert client.post("/auth/forgot-password", json={"email": STAFF_EMAIL}).status_code == 200

    response = client.post(
        "/auth/reset-password",
        json={"token": KNOWN_RAW_TOKEN, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful"

    old_login = client.post(
        "/auth/login", json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD}
    )
    new_login = client.post(
        "/auth/login", json={"email": STAFF_EMAIL, "password": NEW_PASSWORD}
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_reset_password_rejects_reused_token(
    client: TestClient, registered_user: dict, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.routers.auth.secrets.token_urlsafe", lambda _nbytes: KNOWN_RAW_TOKEN
    )
    client.post("/auth/forgot-password", json={"email": STAFF_EMAIL})
    first = client.post(
        "/auth/reset-password",
        json={"token": KNOWN_RAW_TOKEN, "new_password": NEW_PASSWORD},
    )
    assert first.status_code == 200

    reused = client.post(
        "/auth/reset-password",
        json={"token": KNOWN_RAW_TOKEN, "new_password": "AnotherPass9"},
    )

    assert reused.status_code == 400
    assert reused.json()["detail"] == "Invalid or expired token"


def test_reset_password_rejects_unknown_or_expired_token(
    client: TestClient, registered_user: dict
) -> None:
    unknown = client.post(
        "/auth/reset-password",
        json={"token": "unknown-reset-token-value", "new_password": NEW_PASSWORD},
    )
    assert unknown.status_code == 400
    assert unknown.json()["detail"] == "Invalid or expired token"

    import hashlib

    expired_raw = "expired-reset-token-value-32bxx"
    token_hash = hashlib.sha256(expired_raw.encode("utf-8")).hexdigest()
    auth_store.create_reset_token(
        user_id=registered_user["user"]["id"],
        token_hash=token_hash,
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1))
        .replace(microsecond=0)
        .isoformat(),
    )
    # Ensure the stored password is still the original so expiry is the only reason to fail.
    auth_store.update_user(
        registered_user["user"]["id"], hashed_password=hash_password(STAFF_PASSWORD)
    )

    expired = client.post(
        "/auth/reset-password",
        json={"token": expired_raw, "new_password": NEW_PASSWORD},
    )
    assert expired.status_code == 400
    assert expired.json()["detail"] == "Invalid or expired token"
