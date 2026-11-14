"""TinyDB persistence for the centralized incident manager.

Manager writes come from the registration form and ``scripts/seed_incidents.py``.
Analyzer uploads do not mutate this store. ``patient_id`` is never stored.
"""

from __future__ import annotations

import json
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.core.errors import StorageError
from app.models.incidents import IncidentRecord

_SHARED = Path(__file__).resolve().parents[3] / "packages" / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from healthcore_incidents import (  # noqa: E402
    ALLOWED_BRANCHES,
    ALLOWED_CATEGORIES,
    ALLOWED_ORIGINS,
    ALLOWED_STATUSES,
    can_transition,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "incidents.json"

_PUBLIC_FIELDS = (
    "id",
    "title",
    "description",
    "category",
    "status",
    "origin",
    "branch",
    "created_at",
    "updated_at",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db() -> TinyDB:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return TinyDB(DB_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise StorageError("Unable to access incident data store") from exc


def _looks_like_manager_doc(doc: dict[str, Any]) -> bool:
    return "id" in doc and "title" in doc and "branch" in doc and "origin" in doc


def _ensure_manager_schema(db: TinyDB) -> None:
    """Drop legacy analyzer-shaped documents so the manager store stays coherent."""
    docs = db.all()
    if not docs:
        return
    if all(_looks_like_manager_doc(doc) for doc in docs):
        return
    db.truncate()


def _to_record(doc: dict[str, Any]) -> IncidentRecord:
    return IncidentRecord(
        id=doc["id"],
        title=doc["title"],
        description=doc["description"],
        category=doc["category"],
        status=doc["status"],
        origin=doc["origin"],
        branch=doc["branch"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class IncidentExistsError(Exception):
    """An incident with this source_key already exists (seed idempotency)."""


class InvalidTransitionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def create_incident(
    *,
    title: str,
    description: str,
    category: str,
    status: str,
    origin: str,
    branch: str,
    created_at: str | None = None,
    updated_at: str | None = None,
    source_key: str | None = None,
    incident_id: str | None = None,
) -> IncidentRecord:
    if category not in ALLOWED_CATEGORIES:
        raise ValueError("category")
    if status not in ALLOWED_STATUSES:
        raise ValueError("status")
    if origin not in ALLOWED_ORIGINS:
        raise ValueError("origin")
    if branch not in ALLOWED_BRANCHES:
        raise ValueError("branch")

    now = utc_now_iso()
    created = created_at or now
    updated = updated_at or created
    new_id = incident_id or str(uuid.uuid4())

    db = get_db()
    try:
        _ensure_manager_schema(db)
        if source_key:
            existing = db.get(Query().source_key == source_key)
            if existing is not None:
                raise IncidentExistsError(source_key)
        record = {
            "id": new_id,
            "title": title.strip(),
            "description": description.strip(),
            "category": category,
            "status": status,
            "origin": origin,
            "branch": branch,
            "created_at": created,
            "updated_at": updated,
            "source_key": source_key,
        }
        db.insert(record)
        return _to_record(record)
    finally:
        db.close()


def seed_incident(payload: dict[str, Any]) -> str:
    """Insert a transformed seed row. Returns 'inserted' | 'skipped'."""
    source_key = payload["source_key"]
    db = get_db()
    try:
        _ensure_manager_schema(db)
        if db.get(Query().source_key == source_key) is not None:
            return "skipped"
        record = {
            "id": str(uuid.uuid4()),
            "title": payload["title"],
            "description": payload["description"],
            "category": payload["category"],
            "status": payload["status"],
            "origin": payload["origin"],
            "branch": payload["branch"],
            "created_at": payload["created_at"],
            "updated_at": payload["updated_at"],
            "source_key": source_key,
        }
        db.insert(record)
        return "inserted"
    finally:
        db.close()


def update_incident_status(incident_id: str, status: str) -> IncidentRecord:
    if status not in ALLOWED_STATUSES:
        raise ValueError("status")
    db = get_db()
    try:
        _ensure_manager_schema(db)
        existing = db.get(Query().id == incident_id)
        if existing is None:
            raise KeyError(incident_id)
        current = existing["status"]
        if not can_transition(current, status):
            from healthcore_incidents import transition_error

            raise InvalidTransitionError(transition_error(current, status))
        now = utc_now_iso()
        db.update({"status": status, "updated_at": now}, doc_ids=[existing.doc_id])
        updated = db.get(doc_id=existing.doc_id)
        if updated is None:
            raise StorageError("Unable to update this incident. Try again.")
        return _to_record(updated)
    finally:
        db.close()


def get_incident(incident_id: str) -> IncidentRecord | None:
    db = get_db()
    try:
        _ensure_manager_schema(db)
        doc = db.get(Query().id == incident_id)
        return _to_record(doc) if doc else None
    finally:
        db.close()


def list_incidents(
    *,
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
    limit: int = 200,
) -> tuple[int, list[IncidentRecord]]:
    db = get_db()
    try:
        _ensure_manager_schema(db)
        docs = [
            doc
            for doc in db.all()
            if _looks_like_manager_doc(doc)
            and (status is None or doc.get("status") == status)
            and (origin is None or doc.get("origin") == origin)
            and (branch is None or doc.get("branch") == branch)
            and (category is None or doc.get("category") == category)
        ]
    finally:
        db.close()
    docs.sort(key=lambda doc: doc.get("created_at", ""), reverse=True)
    return len(docs), [_to_record(doc) for doc in docs[:limit]]


def summarize_incidents() -> dict[str, Any]:
    db = get_db()
    try:
        _ensure_manager_schema(db)
        docs = [doc for doc in db.all() if _looks_like_manager_doc(doc)]
    finally:
        db.close()

    by_status: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_origin: Counter[str] = Counter()
    by_branch: Counter[str] = Counter()
    for doc in docs:
        by_status[doc["status"]] += 1
        by_category[doc["category"]] += 1
        by_origin[doc["origin"]] += 1
        by_branch[doc["branch"]] += 1

    # Always expose zeroed keys for empty store so clients get a stable shape.
    status_totals = {key: by_status.get(key, 0) for key in sorted(ALLOWED_STATUSES)}
    for key, value in by_status.items():
        status_totals[key] = value
    category_totals = {key: by_category.get(key, 0) for key in sorted(ALLOWED_CATEGORIES)}
    for key, value in by_category.items():
        category_totals[key] = value
    origin_totals = {key: by_origin.get(key, 0) for key in sorted(ALLOWED_ORIGINS)}
    for key, value in by_origin.items():
        origin_totals[key] = value
    branch_totals = {key: by_branch.get(key, 0) for key in sorted(ALLOWED_BRANCHES)}
    for key, value in by_branch.items():
        branch_totals[key] = value

    return {
        "by_status": dict(sorted(status_totals.items())),
        "by_category": dict(sorted((k, v) for k, v in category_totals.items() if v > 0 or not docs)),
        "by_origin": dict(sorted(origin_totals.items())),
        "by_branch": dict(sorted((k, v) for k, v in branch_totals.items() if v > 0 or not docs)),
        "total": len(docs),
    }


def count_by_source_key() -> int:
    db = get_db()
    try:
        _ensure_manager_schema(db)
        return sum(1 for doc in db.all() if doc.get("source_key"))
    finally:
        db.close()
