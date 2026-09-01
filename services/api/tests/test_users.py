"""Owner/admin rules on user mutation (auth module)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.stores import auth_store
from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD


def test_non_owner_cannot_update_another_user(
    client: TestClient, registered_user: dict, auth_headers: dict[str, str]
) -> None:
    other = client.post(
        "/users",
        json={"email": "qa.other@healthcore.example", "password": STAFF_PASSWORD, "name": "Other"},
    )
    assert other.status_code == 201
    other_id = other.json()["user"]["id"]

    response = client.put(
        f"/users/{other_id}",
        headers=auth_headers,
        json={"is_active": False},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_non_admin_cannot_change_role(
    client: TestClient, registered_user: dict, auth_headers: dict[str, str]
) -> None:
    user_id = registered_user["user"]["id"]
    response = client.put(
        f"/users/{user_id}",
        headers=auth_headers,
        json={"role": "admin"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only admin can change role"


def test_admin_can_change_role(
    client: TestClient, registered_user: dict, auth_headers: dict[str, str]
) -> None:
    user_id = registered_user["user"]["id"]
    auth_store.update_user(user_id, role="admin")
    # Token still has role=user in claims; get_current_user loads the store row, not JWT role.
    login = client.post("/auth/login", json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.put(f"/users/{user_id}", headers=headers, json={"role": "manager"})

    assert response.status_code == 200
    assert response.json()["role"] == "manager"
