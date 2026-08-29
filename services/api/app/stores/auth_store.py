"""TinyDB persistence for auth users, profiles, and reset tokens."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.core.errors import StorageError
from app.models.users import UserRole

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "auth.json"

USERS_TABLE = "users"
PROFILES_TABLE = "profiles"
RESET_TOKENS_TABLE = "reset_tokens"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _get_db() -> TinyDB:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        db = TinyDB(DB_PATH)
        # Touch all tables so AUTH-03 can reuse the same store file.
        db.table(USERS_TABLE).all()
        db.table(PROFILES_TABLE).all()
        db.table(RESET_TOKENS_TABLE).all()
        return db
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise StorageError("Unable to access identity data store") from exc


def _serialize_user(doc_id: int, doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc_id,
        "email": doc["email"],
        "is_active": bool(doc.get("is_active", True)),
        "role": doc.get("role", UserRole.user.value),
        "created_at": doc["created_at"],
    }


def _serialize_profile(doc_id: int, doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc_id,
        "user_id": int(doc["user_id"]),
        "name": doc.get("name", ""),
        "phone": doc.get("phone", ""),
        "address": doc.get("address", ""),
    }


def list_users() -> list[dict[str, Any]]:
    db = _get_db()
    try:
        users = db.table(USERS_TABLE)
        return [_serialize_user(doc.doc_id, doc) for doc in users.all()]
    finally:
        db.close()


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    db = _get_db()
    try:
        users = db.table(USERS_TABLE)
        doc = users.get(doc_id=user_id)
        if doc is None:
            return None
        user = _serialize_user(user_id, doc)
        user["hashed_password"] = doc["hashed_password"]
        return user
    finally:
        db.close()


def get_user_by_email(email: str) -> dict[str, Any] | None:
    needle = _normalize_email(email)
    db = _get_db()
    try:
        users = db.table(USERS_TABLE)
        found = next((doc for doc in users if doc.get("email") == needle), None)
        if found is None:
            return None
        user = _serialize_user(found.doc_id, found)
        user["hashed_password"] = found["hashed_password"]
        return user
    finally:
        db.close()


def get_profile_by_user_id(user_id: int) -> dict[str, Any] | None:
    db = _get_db()
    try:
        profiles = db.table(PROFILES_TABLE)
        Profile = Query()
        doc = profiles.get(Profile.user_id == user_id)
        if doc is None:
            return None
        return _serialize_profile(doc.doc_id, doc)
    finally:
        db.close()


def create_user_with_profile(
    *,
    email: str,
    hashed_password: str,
    name: str,
    phone: str,
    address: str,
) -> dict[str, Any]:
    normalized_email = _normalize_email(email)
    db = _get_db()
    try:
        users = db.table(USERS_TABLE)
        profiles = db.table(PROFILES_TABLE)

        existing = next((doc for doc in users if doc.get("email") == normalized_email), None)
        if existing is not None:
            raise ValueError("Email already exists")

        user_record = {
            "email": normalized_email,
            "hashed_password": hashed_password,
            "is_active": True,
            "role": UserRole.user.value,
            "created_at": _utc_now_iso(),
        }
        user_id = users.insert(user_record)

        profile_record = {
            "user_id": user_id,
            "name": name,
            "phone": phone,
            "address": address,
        }
        profile_id = profiles.insert(profile_record)

        return {
            "user": _serialize_user(user_id, user_record),
            "profile": _serialize_profile(profile_id, profile_record),
        }
    finally:
        db.close()


def update_user(
    user_id: int,
    *,
    email: str | None = None,
    hashed_password: str | None = None,
    is_active: bool | None = None,
    role: str | None = None,
) -> dict[str, Any] | None:
    db = _get_db()
    try:
        users = db.table(USERS_TABLE)
        current = users.get(doc_id=user_id)
        if current is None:
            return None

        patch: dict[str, Any] = {}

        if email is not None:
            normalized_email = _normalize_email(email)
            duplicate = next(
                (
                    doc
                    for doc in users
                    if doc.doc_id != user_id and doc.get("email") == normalized_email
                ),
                None,
            )
            if duplicate is not None:
                raise ValueError("Email already exists")
            patch["email"] = normalized_email

        if hashed_password is not None:
            patch["hashed_password"] = hashed_password

        if is_active is not None:
            patch["is_active"] = is_active

        if role is not None:
            patch["role"] = role

        if patch:
            users.update(patch, doc_ids=[user_id])

        refreshed = users.get(doc_id=user_id)
        assert refreshed is not None
        user = _serialize_user(user_id, refreshed)
        user["hashed_password"] = refreshed["hashed_password"]
        return user
    finally:
        db.close()


def delete_user_and_profile(user_id: int) -> bool:
    db = _get_db()
    try:
        users = db.table(USERS_TABLE)
        profiles = db.table(PROFILES_TABLE)
        reset_tokens = db.table(RESET_TOKENS_TABLE)
        Profile = Query()
        ResetToken = Query()

        removed_users = users.remove(doc_ids=[user_id])
        if not removed_users:
            return False

        linked_profile = profiles.get(Profile.user_id == user_id)
        if linked_profile is not None:
            profiles.remove(doc_ids=[linked_profile.doc_id])

        reset_tokens.remove(ResetToken.user_id == user_id)

        return True
    finally:
        db.close()


def update_profile_for_user(
    user_id: int,
    *,
    name: str | None = None,
    phone: str | None = None,
    address: str | None = None,
) -> dict[str, Any] | None:
    db = _get_db()
    try:
        profiles = db.table(PROFILES_TABLE)
        Profile = Query()
        current = profiles.get(Profile.user_id == user_id)
        if current is None:
            return None

        patch: dict[str, Any] = {}
        if name is not None:
            patch["name"] = name
        if phone is not None:
            patch["phone"] = phone
        if address is not None:
            patch["address"] = address

        if patch:
            profiles.update(patch, doc_ids=[current.doc_id])

        refreshed = profiles.get(doc_id=current.doc_id)
        assert refreshed is not None
        return _serialize_profile(current.doc_id, refreshed)
    finally:
        db.close()


def create_reset_token(*, user_id: int, token_hash: str, expires_at: str) -> int:
    db = _get_db()
    try:
        reset_tokens = db.table(RESET_TOKENS_TABLE)
        return reset_tokens.insert(
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "used_at": None,
            }
        )
    finally:
        db.close()


def consume_reset_token(token_hash: str) -> int | None:
    db = _get_db()
    try:
        reset_tokens = db.table(RESET_TOKENS_TABLE)
        ResetToken = Query()
        matches = reset_tokens.search(ResetToken.token_hash == token_hash)
        if not matches:
            return None

        # Prefer the most recent token when duplicates exist.
        token_doc = max(matches, key=lambda item: item.doc_id)
        if token_doc.get("used_at") is not None:
            return None

        try:
            expires_at = datetime.fromisoformat(token_doc["expires_at"])
        except (TypeError, ValueError, KeyError):
            return None
        now = datetime.now(timezone.utc)
        if expires_at <= now:
            return None

        reset_tokens.update(
            {"used_at": _utc_now_iso()},
            doc_ids=[token_doc.doc_id],
        )
        return int(token_doc["user_id"])
    finally:
        db.close()
