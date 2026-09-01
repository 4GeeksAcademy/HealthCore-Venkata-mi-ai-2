"""Current-staff profile read/update."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_and_update_own_profile(
    client: TestClient, registered_user: dict, auth_headers: dict[str, str]
) -> None:
    current = client.get("/profiles/me", headers=auth_headers)
    assert current.status_code == 200
    assert current.json()["user_id"] == registered_user["user"]["id"]

    updated = client.put(
        "/profiles/me",
        headers=auth_headers,
        json={"name": "QA Staff Updated", "phone": "555-0199", "address": "2 Clinic Way"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "QA Staff Updated"


def test_profile_requires_authentication(client: TestClient) -> None:
    response = client.get("/profiles/me")
    assert response.status_code == 401
