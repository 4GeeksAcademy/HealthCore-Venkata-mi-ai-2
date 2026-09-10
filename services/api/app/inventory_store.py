"""TinyDB persistence for HealthCore clinic inventory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.core.errors import StorageError
from app.models.inventory import OrderResponse, OrderType, ProductResponse

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "inventory.json"

PRODUCTS_TABLE = "products"
ORDERS_TABLE = "orders"

SEED_PRODUCTS: list[dict[str, Any]] = [
    {
        "name": "Nitrile exam gloves (box of 100)",
        "sku": "HC-PPE-GLV-100",
        "stock": 12,
        "threshold": 24,
    },
    {
        "name": "Alcohol prep pads (box of 200)",
        "sku": "HC-CLN-PAD-200",
        "stock": 80,
        "threshold": 30,
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def insufficient_stock_detail(available: int, requested: int) -> str:
    return f"Insufficient stock. Available: {available}. Requested: {requested}."


def ensure_data_dir() -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageError("Unable to access inventory data store") from exc


def get_db() -> TinyDB:
    ensure_data_dir()
    try:
        db = TinyDB(DB_PATH)
        db.table(PRODUCTS_TABLE).all()
        db.table(ORDERS_TABLE).all()
        return db
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise StorageError("Unable to access inventory data store") from exc


def _product_from_doc(doc_id: int, doc: dict[str, Any]) -> ProductResponse:
    return ProductResponse(
        id=doc_id,
        name=str(doc["name"]),
        sku=str(doc["sku"]),
        stock=int(doc["stock"]),
        threshold=int(doc["threshold"]),
    )


def _order_from_doc(doc_id: int, doc: dict[str, Any]) -> OrderResponse:
    return OrderResponse(
        id=doc_id,
        product_id=int(doc["product_id"]),
        product_name=str(doc["product_name"]),
        quantity=int(doc["quantity"]),
        type=OrderType(doc["type"]),
        notes=str(doc.get("notes") or ""),
        created_at=str(doc["created_at"]),
        created_by=str(doc["created_by"]),
    )


def list_products() -> list[ProductResponse]:
    db = get_db()
    try:
        products = db.table(PRODUCTS_TABLE)
        return [_product_from_doc(doc.doc_id, doc) for doc in products.all()]
    finally:
        db.close()


def get_product(product_id: int) -> ProductResponse | None:
    db = get_db()
    try:
        doc = db.table(PRODUCTS_TABLE).get(doc_id=product_id)
        if doc is None:
            return None
        return _product_from_doc(product_id, doc)
    finally:
        db.close()


def list_orders() -> list[OrderResponse]:
    db = get_db()
    try:
        orders = db.table(ORDERS_TABLE)
        rows = [_order_from_doc(doc.doc_id, doc) for doc in orders.all()]
        return sorted(rows, key=lambda row: row.created_at, reverse=True)
    finally:
        db.close()


def create_order(
    *,
    product_id: int,
    quantity: int,
    notes: str,
    order_type: OrderType,
    created_by: str,
) -> tuple[OrderResponse | None, str | None]:
    """Return (order, error_detail). error_detail is set on not-found or insufficient stock."""
    db = get_db()
    try:
        products = db.table(PRODUCTS_TABLE)
        product_doc = products.get(doc_id=product_id)
        if product_doc is None:
            return None, "Product not found."

        current_stock = int(product_doc["stock"])
        if order_type is OrderType.outbound and quantity > current_stock:
            return None, insufficient_stock_detail(current_stock, quantity)

        next_stock = (
            current_stock + quantity
            if order_type is OrderType.inbound
            else current_stock - quantity
        )
        products.update({"stock": next_stock}, doc_ids=[product_id])

        record = {
            "product_id": product_id,
            "product_name": product_doc["name"],
            "quantity": quantity,
            "type": order_type.value,
            "notes": notes,
            "created_at": utc_now_iso(),
            "created_by": created_by,
        }
        order_id = db.table(ORDERS_TABLE).insert(record)
        return _order_from_doc(order_id, record), None
    finally:
        db.close()


def seed_inventory() -> int:
    """Insert CONTEXT seed products that are not already present. Returns insert count."""
    db = get_db()
    try:
        products = db.table(PRODUCTS_TABLE)
        Product = Query()
        inserted = 0
        for row in SEED_PRODUCTS:
            existing = products.search(Product.sku == row["sku"])
            if existing:
                continue
            products.insert(dict(row))
            inserted += 1
        return inserted
    finally:
        db.close()
