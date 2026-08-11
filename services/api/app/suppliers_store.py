"""TinyDB persistence for HealthCore suppliers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.models.suppliers import (
    Country,
    ProductCategory,
    SupplierCreate,
    SupplierResponse,
    SupplierStatus,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "suppliers.json"

SEED_SUPPLIERS: list[dict[str, Any]] = [
    {
        "name": "MediSupply Austin",
        "country": "US",
        "product_categories": ["MEDICAL_SUPPLIES", "PPE"],
        "contract_rate": 12.50,
        "status": "active",
    },
    {
        "name": "Lone Star Lab Kits",
        "country": "US",
        "product_categories": ["LAB_CONSUMABLES"],
        "contract_rate": 8.75,
        "status": "active",
    },
    {
        "name": "Thames Diagnostics Ltd",
        "country": "UK",
        "product_categories": ["DIAGNOSTIC_EQUIPMENT", "LAB_CONSUMABLES"],
        "contract_rate": 120.00,
        "status": "active",
    },
    {
        "name": "Northbridge Facilities Co",
        "country": "UK",
        "product_categories": ["FACILITIES"],
        "contract_rate": 45.00,
        "status": "suspended",
    },
    {
        "name": "Gulf Coast Pharma Wholesale",
        "country": "US",
        "product_categories": ["PHARMACEUTICALS"],
        "contract_rate": 22.00,
        "status": "active",
    },
    {
        "name": "Heathrow Clinic IT Partners",
        "country": "UK",
        "product_categories": ["IT_EQUIPMENT"],
        "contract_rate": 89.99,
        "status": "active",
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
        product_categories=[ProductCategory(c) for c in doc["product_categories"]],
        contract_rate=float(doc["contract_rate"]),
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
            cats = doc.get("product_categories") or []
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
            "product_categories": [c.value for c in payload.product_categories],
            "contract_rate": payload.contract_rate,
            "updated_at": utc_now_iso(),
            "status": payload.status.value,
        }
        doc_id = db.insert(record)
        return _doc_to_response(doc_id, record)
    finally:
        db.close()


def update_rate(supplier_id: int, contract_rate: float) -> SupplierResponse | None:
    db = get_db()
    try:
        doc = db.get(doc_id=supplier_id)
        if doc is None:
            return None
        updated_at = utc_now_iso()
        db.update(
            {"contract_rate": contract_rate, "updated_at": updated_at},
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


def seed_suppliers() -> int:
    """Insert CONTEXT seed rows that are not already present. Returns insert count."""
    db = get_db()
    try:
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
