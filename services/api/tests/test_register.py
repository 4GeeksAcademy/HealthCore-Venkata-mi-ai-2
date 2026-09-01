"""POST /users — staff registration decisions."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD


def test_register_creates_active_user_with_profile(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD,
            "name": "QA Staff",
            "phone": "555-0100",
            "address": "1 Clinic Way",
        },
    )

    assert response.status_code == 201
    body = response.json()
    user = body["user"]
    profile = body["profile"]

    assert user["email"] == STAFF_EMAIL
    assert user["role"] == "user"
    assert user["is_active"] is True
    assert "hashed_password" not in user
    assert "password" not in user
    assert profile["user_id"] == user["id"]
    assert profile["name"] == "QA Staff"


def test_register_rejects_duplicate_email_regardless_of_case(client: TestClient) -> None:
    first = client.post(
        "/users",
        json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD, "name": "QA Staff"},
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/users",
        json={"email": "  QA.STAFF@healthcore.example  ", "password": "OtherPass9"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email already exists"


def test_register_accepts_minimum_password_length(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={"email": "qa.boundary@healthcore.example", "password": "Pass1234"},
    )

    assert response.status_code == 201
    assert response.json()["user"]["is_active"] is True


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/users",
        json={"email": "qa.short@healthcore.example", "password": "short7"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid request. Please check the submitted data."
