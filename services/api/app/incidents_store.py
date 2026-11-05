"""TinyDB persistence for individual incidents ingested through the analyzer.

Only rows that pass ``incident_analysis.validate_row`` are stored. A re-upload of
the same ``incident_id`` updates the record, so readers always see the latest
status the incident manager received.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.core.errors import StorageError
from app.models.incidents import IncidentRecord

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "incidents.json"

_STORED_FIELDS = ("incident_id", "clinic_id", "country", "patient_id", "category", "status")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db() -> TinyDB:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return TinyDB(DB_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise StorageError("Unable to access incident data store") from exc


def _score(raw: str | None) -> float | None:
    try:
        return float(raw) if raw not in (None, "") else None
    except ValueError:
        return None


def _to_record(doc: dict[str, Any]) -> IncidentRecord:
    # patient_id is stored with the incident but never leaves the store.
    return IncidentRecord(
        incident_id=doc["incident_id"],
        clinic_id=doc["clinic_id"],
        country=doc["country"],
        category=doc["category"],
        status=doc["status"],
        satisfaction_score=doc.get("satisfaction_score"),
        source_file=doc.get("source_file", ""),
        first_recorded_at=doc["first_recorded_at"],
        updated_at=doc["updated_at"],
    )


def upsert_incidents(rows: list[dict[str, str]], *, source_file: str) -> int:
    """Insert or update validated rows keyed by ``incident_id``. Returns rows written."""
    now = utc_now_iso()
    incident = Query()
    db = get_db()
    try:
        for row in rows:
            record = {field: row[field].strip() for field in _STORED_FIELDS}
            record["satisfaction_score"] = _score(row.get("satisfaction_score"))
            record["source_file"] = source_file
            record["updated_at"] = now
            existing = db.get(incident.incident_id == record["incident_id"])
            if existing is None:
                db.insert({**record, "first_recorded_at": now})
            else:
                db.update(record, doc_ids=[existing.doc_id])
        return len(rows)
    finally:
        db.close()


def get_incident(incident_id: str) -> IncidentRecord | None:
    db = get_db()
    try:
        doc = db.get(Query().incident_id == incident_id)
        return _to_record(doc) if doc else None
    finally:
        db.close()


def list_incidents(
    *,
    status: str | None = None,
    category: str | None = None,
    clinic_id: str | None = None,
    country: str | None = None,
    limit: int = 50,
) -> tuple[int, list[IncidentRecord]]:
    """Matching incidents ordered by id, plus the total before ``limit``."""
    db = get_db()
    try:
        docs = [
            doc
            for doc in db.all()
            if (status is None or doc.get("status") == status)
            and (category is None or doc.get("category") == category)
            and (clinic_id is None or doc.get("clinic_id") == clinic_id)
            and (country is None or doc.get("country") == country)
        ]
    finally:
        db.close()
    docs.sort(key=lambda doc: doc["incident_id"])
    return len(docs), [_to_record(doc) for doc in docs[:limit]]
