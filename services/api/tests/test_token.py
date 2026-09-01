"""GET /auth/me — JWT session identity decisions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from jose import jwt

from tests.conftest import TEST_JWT_SECRET


def test_me_returns_staff_and_profile_for_valid_token(
    client: TestClient, registered_user: dict, auth_headers: dict[str, str]
) -> None:
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == registered_user["user"]["id"]
    assert body["email"] == registered_user["user"]["email"]
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert body["profile"]["user_id"] == body["id"]


def test_me_rejects_token_after_staff_is_deleted(
    client: TestClient, registered_user: dict, auth_headers: dict[str, str]
) -> None:
    user_id = registered_user["user"]["id"]
    deleted = client.delete(f"/users/{user_id}", headers=auth_headers)
    assert deleted.status_code == 200

    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_me_rejects_missing_garbage_or_expired_token(client: TestClient, registered_user: dict) -> None:
    missing = client.get("/auth/me")
    garbage = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    expired = jwt.encode(
        {
            "sub": str(registered_user["user"]["id"]),
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    expired_response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )

    assert missing.status_code == 401
    assert garbage.status_code == 401
    assert expired_response.status_code == 401
    assert garbage.json()["detail"] == "Could not validate credentials"
    assert expired_response.json()["detail"] == "Could not validate credentials"


def test_me_rejects_token_without_subject(client: TestClient) -> None:
    token = jwt.encode(
        {
            "role": "user",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
