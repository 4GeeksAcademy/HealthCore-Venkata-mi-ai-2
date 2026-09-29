"""TinyDB persistence for clinic inventory when INVENTORY_BACKEND=tinydb."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.core.errors import StorageError
from app.inventory.schemas import (
    InboundOrderResponse,
    InventoryOrderResponse,
    MedicalSupplyResponse,
    OrderType,
    OutboundOrderResponse,
)
from app.inventory.service import (
    SEED_ROWS,
    SEED_USER_UUID,
    creator_email,
    insufficient_stock_detail,
    threshold_crossed,
    utc_now,
    iso_timestamp,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "inventory.json"

PRODUCTS = "products"
INBOUND = "inbound_orders"
OUTBOUND = "outbound_orders"


def _db() -> TinyDB:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return TinyDB(DB_PATH)
    except OSError as exc:
        raise StorageError("Unable to access inventory data store") from exc


def _next_id(table_name: str) -> int:
    table = _db().table(table_name)
    rows = table.all()
    return max((int(row.get("id", 0)) for row in rows), default=0) + 1


def current_stock(product_id: int) -> int:
    db = _db()
    inbound = sum(
        int(row["quantity"])
        for row in db.table(INBOUND).all()
        if int(row["product_id"]) == product_id
    )
    outbound = sum(
        int(row["quantity"])
        for row in db.table(OUTBOUND).all()
        if int(row["product_id"]) == product_id
    )
    return inbound - outbound


def _product_doc(product_id: int) -> dict[str, Any] | None:
    Product = Query()
    found = _db().table(PRODUCTS).search(Product.id == product_id)
    return found[0] if found else None


def list_products() -> list[MedicalSupplyResponse]:
    rows = sorted(_db().table(PRODUCTS).all(), key=lambda row: int(row["id"]))
    return [
        MedicalSupplyResponse(
            id=int(row["id"]),
            name=str(row["name"]),
            sku=str(row["sku"]),
            threshold=int(row["threshold"]),
            current_stock=current_stock(int(row["id"])),
        )
        for row in rows
    ]


def get_product(product_id: int) -> MedicalSupplyResponse | None:
    row = _product_doc(product_id)
    if row is None:
        return None
    return MedicalSupplyResponse(
        id=int(row["id"]),
        name=str(row["name"]),
        sku=str(row["sku"]),
        threshold=int(row["threshold"]),
        current_stock=current_stock(product_id),
    )


def create_product(*, name: str, sku: str, threshold: int) -> MedicalSupplyResponse:
    Product = Query()
    if _db().table(PRODUCTS).search(Product.sku == sku):
        raise ValueError("SKU already exists.")
    product_id = _next_id(PRODUCTS)
    _db().table(PRODUCTS).insert(
        {"id": product_id, "name": name, "sku": sku, "threshold": threshold}
    )
    return MedicalSupplyResponse(
        id=product_id,
        name=name,
        sku=sku,
        threshold=threshold,
        current_stock=0,
    )


def create_inbound(
    *,
    product_id: int,
    quantity: int,
    notes: str,
    user_uuid: str,
    user_email: str,
) -> InboundOrderResponse:
    product = _product_doc(product_id)
    if product is None:
        raise LookupError("Product not found.")
    order_id = _next_id(INBOUND)
    created = utc_now()
    _db().table(INBOUND).insert(
        {
            "id": order_id,
            "product_id": product_id,
            "product_name": product["name"],
            "sku": product["sku"],
            "quantity": quantity,
            "notes": notes,
            "created_at": created.isoformat(),
            "user_uuid": user_uuid,
        }
    )
    return InboundOrderResponse(
        id=order_id,
        product_id=product_id,
        product_name=str(product["name"]),
        quantity=quantity,
        notes=notes,
        created_at=iso_timestamp(created),
        user_uuid=user_uuid,
        created_by=user_email or user_uuid,
    )


def create_outbound(
    *,
    product_id: int,
    quantity: int,
    notes: str,
    user_uuid: str,
    user_email: str,
) -> OutboundOrderResponse:
    product = _product_doc(product_id)
    if product is None:
        raise LookupError("Product not found.")
    previous_stock = current_stock(product_id)
    if quantity > previous_stock:
        raise ValueError(insufficient_stock_detail(previous_stock, quantity))
    order_id = _next_id(OUTBOUND)
    created = utc_now()
    _db().table(OUTBOUND).insert(
        {
            "id": order_id,
            "product_id": product_id,
            "product_name": product["name"],
            "sku": product["sku"],
            "quantity": quantity,
            "notes": notes,
            "created_at": created.isoformat(),
            "user_uuid": user_uuid,
        }
    )
    current = current_stock(product_id)
    threshold = int(product["threshold"])
    return OutboundOrderResponse(
        id=order_id,
        product_id=product_id,
        product_name=str(product["name"]),
        quantity=quantity,
        notes=notes,
        created_at=iso_timestamp(created),
        user_uuid=user_uuid,
        created_by=user_email or user_uuid,
        sku=str(product["sku"]),
        threshold=threshold,
        previous_stock=previous_stock,
        current_stock=current,
        threshold_crossed=threshold_crossed(previous_stock, current, threshold),
    )


def list_orders() -> list[InventoryOrderResponse]:
    combined: list[InventoryOrderResponse] = []
    for row in _db().table(INBOUND).all():
        combined.append(
            InventoryOrderResponse(
                id=int(row["id"]),
                product_id=int(row["product_id"]),
                product_name=str(row.get("product_name") or ""),
                quantity=int(row["quantity"]),
                type=OrderType.inbound,
                notes=str(row.get("notes") or ""),
                created_at=str(row["created_at"]),
                user_uuid=str(row["user_uuid"]),
                created_by=creator_email(str(row["user_uuid"])),
            )
        )
    for row in _db().table(OUTBOUND).all():
        combined.append(
            InventoryOrderResponse(
                id=int(row["id"]),
                product_id=int(row["product_id"]),
                product_name=str(row.get("product_name") or ""),
                quantity=int(row["quantity"]),
                type=OrderType.outbound,
                notes=str(row.get("notes") or ""),
                created_at=str(row["created_at"]),
                user_uuid=str(row["user_uuid"]),
                created_by=creator_email(str(row["user_uuid"])),
            )
        )
    combined.sort(key=lambda item: item.created_at, reverse=True)
    return combined


def seed_inventory() -> int:
    """Insert CONTEXT seed supplies. Idempotent on sku."""
    Product = Query()
    inserted = 0
    for item in SEED_ROWS:
        if _db().table(PRODUCTS).search(Product.sku == item["sku"]):
            continue
        created = create_product(
            name=str(item["name"]),
            sku=str(item["sku"]),
            threshold=int(item["threshold"]),
        )
        create_inbound(
            product_id=created.id,
            quantity=int(item["inbound"]),
            notes=str(item["inbound_notes"]),
            user_uuid=SEED_USER_UUID,
            user_email=creator_email(SEED_USER_UUID),
        )
        outbound_qty = int(item["outbound"])
        if outbound_qty > 0:
            create_outbound(
                product_id=created.id,
                quantity=outbound_qty,
                notes=str(item["outbound_notes"]),
                user_uuid=SEED_USER_UUID,
                user_email=creator_email(SEED_USER_UUID),
            )
        inserted += 1
    return inserted


def init_store() -> None:
    """Ensure the JSON file exists."""
    _db()
