"""POST /auth/login — who may receive a session token."""

from __future__ import annotations

from jose import jwt
from fastapi.testclient import TestClient

from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD, TEST_JWT_SECRET
from app.stores import auth_store


def test_login_issues_bearer_token_for_active_staff(
    client: TestClient, registered_user: dict
) -> None:
    response = client.post(
        "/auth/login",
        json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    claims = jwt.decode(body["access_token"], TEST_JWT_SECRET, algorithms=["HS256"])
    assert claims["sub"] == str(registered_user["user"]["id"])
    assert claims["role"] == "user"


def test_login_rejects_inactive_staff_with_correct_password(
    client: TestClient, registered_user: dict
) -> None:
    auth_store.update_user(registered_user["user"]["id"], is_active=False)

    response = client.post(
        "/auth/login",
        json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Inactive user"
    assert "access_token" not in response.json()


def test_login_rejects_unknown_or_wrong_password(client: TestClient, registered_user: dict) -> None:
    wrong_password = client.post(
        "/auth/login",
        json={"email": STAFF_EMAIL, "password": "WrongPass9"},
    )
    unknown_email = client.post(
        "/auth/login",
        json={"email": "nobody@healthcore.example", "password": STAFF_PASSWORD},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid credentials"
    assert unknown_email.json()["detail"] == "Invalid credentials"
