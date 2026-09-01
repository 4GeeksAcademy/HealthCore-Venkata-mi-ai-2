"""Password hashing and JWT decode decisions (auth module helpers)."""

from __future__ import annotations

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_verifies_matching_secret_only() -> None:
    hashed = hash_password("StaffPass9")

    assert hashed != "StaffPass9"
    assert verify_password("StaffPass9", hashed) is True
    assert verify_password("WrongPass9", hashed) is False


def test_decode_access_token_rejects_invalid_or_tampered_token() -> None:
    token = create_access_token(subject="1", role="user")
    claims = decode_access_token(token)
    assert claims["sub"] == "1"
    assert claims["role"] == "user"

    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_access_token("not-a-jwt")
