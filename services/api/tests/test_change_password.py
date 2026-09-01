"""POST /auth/change-password — authenticated password replacement."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD

NEW_PASSWORD = "ChangedPass9"


def test_change_password_updates_credentials_for_authenticated_staff(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/auth/change-password",
        headers=auth_headers,
        json={"current_password": STAFF_PASSWORD, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    old_login = client.post(
        "/auth/login", json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD}
    )
    new_login = client.post(
        "/auth/login", json={"email": STAFF_EMAIL, "password": NEW_PASSWORD}
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/auth/change-password",
        headers=auth_headers,
        json={"current_password": "WrongPass9", "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"

    still_old = client.post(
        "/auth/login", json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD}
    )
    assert still_old.status_code == 200


def test_change_password_rejects_unauthenticated_request(client: TestClient) -> None:
    response = client.post(
        "/auth/change-password",
        json={"current_password": STAFF_PASSWORD, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 401
