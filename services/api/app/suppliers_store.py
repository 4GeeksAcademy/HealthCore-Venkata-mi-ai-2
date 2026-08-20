"""TinyDB persistence for HealthCore suppliers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.models.suppliers import (
    Country,
    Currency,
    ProductCategory,
    SupplierCreate,
    SupplierResponse,
    SupplierStatus,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "suppliers.json"

SEED_SUPPLIERS: list[dict[str, Any]] = [
    {
        "name": "McKesson",
        "country": "USA",
        "categories": ["MEDICAL_SUPPLIES", "PHARMACEUTICALS"],
        "monthly_rate": 48500.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Epic",
        "country": "USA",
        "categories": ["IT_EQUIPMENT"],
        "monthly_rate": 125000.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Cardinal Health",
        "country": "USA",
        "categories": ["MEDICAL_SUPPLIES"],
        "monthly_rate": 31200.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Henry Schein",
        "country": "USA",
        "categories": ["MEDICAL_SUPPLIES", "PPE"],
        "monthly_rate": 18450.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Medline",
        "country": "USA",
        "categories": ["PPE", "MEDICAL_SUPPLIES"],
        "monthly_rate": 22100.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Quest Diagnostics",
        "country": "USA",
        "categories": ["LAB_CONSUMABLES"],
        "monthly_rate": 15800.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "BD",
        "country": "USA",
        "categories": ["DIAGNOSTIC_EQUIPMENT", "LAB_CONSUMABLES"],
        "monthly_rate": 27600.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Owens and Minor",
        "country": "USA",
        "categories": ["MEDICAL_SUPPLIES"],
        "monthly_rate": 14320.00,
        "currency": "USD",
        "status": "active",
    },
    {
        "name": "Stericycle",
        "country": "USA",
        "categories": ["FACILITIES"],
        "monthly_rate": 8900.00,
        "currency": "USD",
        "status": "suspended",
    },
    {
        "name": "EMIS Health",
        "country": "UK",
        "categories": ["IT_EQUIPMENT"],
        "monthly_rate": 42000.00,
        "currency": "GBP",
        "status": "active",
    },
    {
        "name": "TPP",
        "country": "UK",
        "categories": ["IT_EQUIPMENT"],
        "monthly_rate": 38500.00,
        "currency": "GBP",
        "status": "active",
    },
    {
        "name": "Phoenix Medical Supplies",
        "country": "UK",
        "categories": ["PHARMACEUTICALS"],
        "monthly_rate": 19600.00,
        "currency": "GBP",
        "status": "active",
    },
    {
        "name": "Alliance Healthcare",
        "country": "UK",
        "categories": ["PHARMACEUTICALS", "MEDICAL_SUPPLIES"],
        "monthly_rate": 24800.00,
        "currency": "GBP",
        "status": "active",
    },
    {
        "name": "Siemens Healthineers",
        "country": "UK",
        "categories": ["DIAGNOSTIC_EQUIPMENT"],
        "monthly_rate": 54000.00,
        "currency": "GBP",
        "status": "active",
    },
    {
        "name": "ISS Healthcare",
        "country": "UK",
        "categories": ["FACILITIES"],
        "monthly_rate": 11200.00,
        "currency": "GBP",
        "status": "suspended",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_db() -> TinyDB:
    ensure_data_dir()
    return TinyDB(DB_PATH)


def _doc_to_response(doc_id: int, doc: dict[str, Any]) -> SupplierResponse:
    return SupplierResponse(
        id=doc_id,
        name=doc["name"],
        country=Country(doc["country"]),
        categories=[ProductCategory(c) for c in doc["categories"]],
        monthly_rate=float(doc["monthly_rate"]),
        currency=Currency(doc["currency"]),
        updated_at=doc["updated_at"],
        status=SupplierStatus(doc["status"]),
    )


def list_suppliers(
    country: str | None = None,
    category: str | None = None,
) -> list[SupplierResponse]:
    db = get_db()
    try:
        results: list[SupplierResponse] = []
        for doc in db.all():
            doc_id = doc.doc_id
            if country is not None and doc.get("country") != country:
                continue
            cats = doc.get("categories") or []
            if category is not None and category not in cats:
                continue
            results.append(_doc_to_response(doc_id, doc))
        return results
    finally:
        db.close()


def get_supplier(supplier_id: int) -> SupplierResponse | None:
    db = get_db()
    try:
        doc = db.get(doc_id=supplier_id)
        if doc is None:
            return None
        return _doc_to_response(supplier_id, doc)
    finally:
        db.close()


def create_supplier(payload: SupplierCreate) -> SupplierResponse:
    db = get_db()
    try:
        record = {
            "name": payload.name,
            "country": payload.country.value,
            "categories": [c.value for c in payload.categories],
            "monthly_rate": payload.monthly_rate,
            "currency": payload.currency.value,
            "updated_at": utc_now_iso(),
            "status": payload.status.value,
        }
        doc_id = db.insert(record)
        return _doc_to_response(doc_id, record)
    finally:
        db.close()


def update_rate(supplier_id: int, monthly_rate: float) -> SupplierResponse | None:
    db = get_db()
    try:
        doc = db.get(doc_id=supplier_id)
        if doc is None:
            return None
        updated_at = utc_now_iso()
        db.update(
            {"monthly_rate": monthly_rate, "updated_at": updated_at},
            doc_ids=[supplier_id],
        )
        refreshed = db.get(doc_id=supplier_id)
        assert refreshed is not None
        return _doc_to_response(supplier_id, refreshed)
    finally:
        db.close()


def update_status(supplier_id: int, status: SupplierStatus) -> SupplierResponse | None:
    db = get_db()
    try:
        doc = db.get(doc_id=supplier_id)
        if doc is None:
            return None
        updated_at = utc_now_iso()
        db.update(
            {"status": status.value, "updated_at": updated_at},
            doc_ids=[supplier_id],
        )
        refreshed = db.get(doc_id=supplier_id)
        assert refreshed is not None
        return _doc_to_response(supplier_id, refreshed)
    finally:
        db.close()


def delete_supplier(supplier_id: int) -> bool:
    db = get_db()
    try:
        removed = db.remove(doc_ids=[supplier_id])
        return len(removed) > 0
    finally:
        db.close()


def _is_legacy_schema(doc: dict[str, Any]) -> bool:
    """True for pre-syllabus rows (contract_rate / US / product_categories)."""
    return (
        "contract_rate" in doc
        or "product_categories" in doc
        or doc.get("country") == "US"
    )


def seed_suppliers() -> int:
    """Insert CONTEXT seed rows that are not already present. Returns insert count."""
    db = get_db()
    try:
        if any(_is_legacy_schema(doc) for doc in db.all()):
            db.truncate()
        Supplier = Query()
        inserted = 0
        now = utc_now_iso()
        for row in SEED_SUPPLIERS:
            existing = db.search(
                (Supplier.name == row["name"]) & (Supplier.country == row["country"])
            )
            if existing:
                continue
            db.insert({**row, "updated_at": now})
            inserted += 1
        return inserted
    finally:
        db.close()
