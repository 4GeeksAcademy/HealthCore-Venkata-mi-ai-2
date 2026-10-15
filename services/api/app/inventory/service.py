"""Inventory domain helpers: computed stock, seed, order mapping."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, func, select

from app.core.errors import StorageError
from app.inventory.models import InboundOrder, MedicalSupply, OutboundOrder
from app.inventory.schemas import (
    InventoryOrderResponse,
    MedicalSupplyResponse,
    OrderType,
)

SEED_USER_UUID = "1"
DEFAULT_CLINIC_ID = "us-tx-001"
DEFAULT_COUNTRY = "US"
DEFAULT_DEPARTMENT = "general_consultation"
DEFAULT_CATEGORY = "consumable"
EXPIRY_FLAG_DAYS = 30

# CONTEXT-healthcore §5: ≥8–10 SKUs across 4 categories; US + UK clinics; threshold/expiry cases.
SEED_ROWS: list[dict] = [
    {
        "name": "Nitrile exam gloves (box of 100)",
        "sku": "HC-PPE-GLV-100",
        "threshold": 24,
        "category": "ppe",
        "expiry_date": None,
        "clinic_id": "us-tx-001",
        "country": "US",
        "department": "general_consultation",
        "inbound": 40,
        "outbound": 28,
        "inbound_notes": "McKesson delivery — Austin clinic restock",
        "outbound_notes": "Manchester clinic weekly consumption",
        "total_cost": 48.0,
    },
    {
        "name": "Alcohol prep pads (box of 200)",
        "sku": "HC-CLN-PAD-200",
        "threshold": 30,
        "category": "consumable",
        "expiry_date": None,
        "clinic_id": "us-tx-001",
        "country": "US",
        "department": "general_consultation",
        "inbound": 80,
        "outbound": 0,
        "inbound_notes": "Clinic restock",
        "outbound_notes": "",
        "total_cost": 22.5,
    },
    {
        "name": "5ml syringes (box of 100)",
        "sku": "HC-CON-SYR-5ML",
        "threshold": 40,
        "category": "consumable",
        "expiry_date": None,
        "clinic_id": "us-fl-001",
        "country": "US",
        "department": "chronic_care",
        "inbound": 120,
        "outbound": 35,
        "inbound_notes": "Florida clinic consumables",
        "outbound_notes": "Chronic care draw-downs",
        "total_cost": 55.0,
    },
    {
        "name": "Surgical masks (box of 50)",
        "sku": "HC-PPE-MSK-50",
        "threshold": 20,
        "category": "ppe",
        "expiry_date": None,
        "clinic_id": "uk-lon-001",
        "country": "UK",
        "department": "general_consultation",
        "inbound": 60,
        "outbound": 45,
        "inbound_notes": "London PPE restock",
        "outbound_notes": "Primary care use",
        "total_cost": 30.0,
    },
    {
        "name": "Flu vaccine (single dose)",
        "sku": "HC-MED-FLU-01",
        "threshold": 15,
        "category": "medication",
        "expiry_date": "relative:+20",
        "clinic_id": "us-tx-001",
        "country": "US",
        "department": "preventive",
        "inbound": 40,
        "outbound": 10,
        "inbound_notes": "Seasonal flu stock",
        "outbound_notes": "Preventive clinic",
        "total_cost": 400.0,
    },
    {
        "name": "Amoxicillin 500mg (pack 21)",
        "sku": "HC-MED-AMX-500",
        "threshold": 12,
        "category": "medication",
        "expiry_date": "relative:+90",
        "clinic_id": "uk-man-001",
        "country": "UK",
        "department": "general_consultation",
        "inbound": 30,
        "outbound": 8,
        "inbound_notes": "Manchester pharmacy inbound",
        "outbound_notes": "Outpatient scripts",
        "total_cost": 95.0,
    },
    {
        "name": "Digital thermometer",
        "sku": "HC-EQP-THM-01",
        "threshold": 5,
        "category": "equipment",
        "expiry_date": None,
        "clinic_id": "us-ga-001",
        "country": "US",
        "department": "general_consultation",
        "inbound": 12,
        "outbound": 2,
        "inbound_notes": "Georgia equipment intake",
        "outbound_notes": "Room assignment",
        "total_cost": 180.0,
    },
    {
        "name": "Pulse oximeter",
        "sku": "HC-EQP-OXM-01",
        "threshold": 4,
        "category": "equipment",
        "expiry_date": None,
        "clinic_id": "uk-lon-001",
        "country": "UK",
        "department": "specialty_care",
        "inbound": 10,
        "outbound": 1,
        "inbound_notes": "London specialty kit",
        "outbound_notes": "Specialty loan",
        "total_cost": 250.0,
    },
    {
        "name": "Wound dressing sterile 10x10",
        "sku": "HC-CON-WND-10",
        "threshold": 25,
        "category": "consumable",
        "expiry_date": "relative:+25",
        "clinic_id": "us-fl-001",
        "country": "US",
        "department": "specialty_care",
        "inbound": 50,
        "outbound": 30,
        "inbound_notes": "Wound-care consumables",
        "outbound_notes": "Dressing clinic",
        "total_cost": 75.0,
    },
    {
        "name": "Hand sanitizer 500ml",
        "sku": "HC-CLN-SAN-500",
        "threshold": 18,
        "category": "consumable",
        "expiry_date": None,
        "clinic_id": "uk-man-001",
        "country": "UK",
        "department": "general_consultation",
        "inbound": 36,
        "outbound": 20,
        "inbound_notes": "Infection control stock",
        "outbound_notes": "Room restock",
        "total_cost": 42.0,
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def parse_expiry(raw: str | date | None) -> date | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    text = str(raw).strip()
    if text.startswith("relative:"):
        days = int(text.split(":", 1)[1])
        return datetime.now(timezone.utc).date() + timedelta(days=days)
    return date.fromisoformat(text)


def format_expiry(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def days_to_expiry(value: date | None, *, today: date | None = None) -> int | None:
    if value is None:
        return None
    base = today or datetime.now(timezone.utc).date()
    return (value - base).days


def expiry_flag_due(value: date | None, *, today: date | None = None) -> bool:
    remaining = days_to_expiry(value, today=today)
    return remaining is not None and 0 <= remaining <= EXPIRY_FLAG_DAYS


def creator_email(user_uuid: str) -> str:
    """Resolve TinyDB staff email for UI/reporting. Not stored in SQLModel/Supabase."""
    from app.stores import auth_store

    try:
        user_id = int(user_uuid)
    except (TypeError, ValueError):
        return user_uuid
    user = auth_store.get_user_by_id(user_id)
    if user is None:
        return user_uuid
    email = user.get("email")
    return str(email) if email else user_uuid


def insufficient_stock_detail(available: int, requested: int) -> str:
    return f"Insufficient stock. Available: {available}. Requested: {requested}."


DIRECT_STOCK_EDIT_DETAIL = (
    "Stock cannot be modified directly. Register an inbound or outbound order."
)


def threshold_crossed(previous: int, current: int, threshold: int) -> bool:
    """True only when stock moves from at-or-above the restock line to below it."""
    return previous >= threshold and current < threshold


def _sum_qty(session: Session, model: type[InboundOrder] | type[OutboundOrder], product_id: int) -> int:
    total = session.exec(
        select(func.coalesce(func.sum(model.quantity), 0)).where(model.product_id == product_id)
    ).one()
    return int(total or 0)


def current_stock_for(session: Session, product_id: int) -> int:
    inbound = _sum_qty(session, InboundOrder, product_id)
    outbound = _sum_qty(session, OutboundOrder, product_id)
    return inbound - outbound


def stock_map(session: Session) -> dict[int, int]:
    inbound_rows = session.exec(
        select(InboundOrder.product_id, func.coalesce(func.sum(InboundOrder.quantity), 0)).group_by(
            InboundOrder.product_id
        )
    ).all()
    outbound_rows = session.exec(
        select(OutboundOrder.product_id, func.coalesce(func.sum(OutboundOrder.quantity), 0)).group_by(
            OutboundOrder.product_id
        )
    ).all()
    inbound = {int(pid): int(qty or 0) for pid, qty in inbound_rows}
    outbound = {int(pid): int(qty or 0) for pid, qty in outbound_rows}
    product_ids = set(inbound) | set(outbound)
    return {pid: inbound.get(pid, 0) - outbound.get(pid, 0) for pid in product_ids}


def to_supply_response(row: MedicalSupply, stock: int) -> MedicalSupplyResponse:
    assert row.id is not None
    category = getattr(row, "category", None) or DEFAULT_CATEGORY
    expiry = getattr(row, "expiry_date", None)
    return MedicalSupplyResponse(
        id=row.id,
        name=row.name,
        sku=row.sku,
        threshold=row.threshold,
        current_stock=stock,
        category=str(category),
        expiry_date=format_expiry(expiry),
    )


def to_order_response(
    row: InboundOrder | OutboundOrder,
    order_type: OrderType,
) -> InventoryOrderResponse:
    assert row.id is not None
    product_name = row.product_name or (row.product.name if row.product is not None else "")
    clinic_id = getattr(row, "clinic_id", None) or DEFAULT_CLINIC_ID
    country = getattr(row, "country", None) or DEFAULT_COUNTRY
    department = getattr(row, "department", None) if order_type == OrderType.outbound else None
    return InventoryOrderResponse(
        id=row.id,
        product_id=row.product_id,
        product_name=product_name,
        quantity=row.quantity,
        type=order_type,
        notes=row.notes,
        created_at=iso_timestamp(row.created_at),
        user_uuid=row.user_uuid,
        created_by=creator_email(row.user_uuid),
        clinic_id=str(clinic_id),
        country=str(country),
        department=str(department) if department else None,
    )


def list_supplies(session: Session) -> list[MedicalSupplyResponse]:
    try:
        rows = session.exec(select(MedicalSupply).order_by(col(MedicalSupply.id))).all()
        stocks = stock_map(session)
        return [to_supply_response(row, stocks.get(row.id or 0, 0)) for row in rows]
    except SQLAlchemyError as exc:
        raise StorageError("Unable to access inventory data store") from exc


def get_supply(session: Session, product_id: int) -> MedicalSupplyResponse | None:
    try:
        row = session.get(MedicalSupply, product_id)
        if row is None:
            return None
        return to_supply_response(row, current_stock_for(session, product_id))
    except SQLAlchemyError as exc:
        raise StorageError("Unable to access inventory data store") from exc


def list_orders(session: Session) -> list[InventoryOrderResponse]:
    try:
        inbound = session.exec(
            select(InboundOrder).options(selectinload(InboundOrder.product))
        ).all()
        outbound = session.exec(
            select(OutboundOrder).options(selectinload(OutboundOrder.product))
        ).all()
        combined = [to_order_response(row, OrderType.inbound) for row in inbound]
        combined.extend(to_order_response(row, OrderType.outbound) for row in outbound)
        combined.sort(key=lambda item: item.created_at, reverse=True)
        return combined
    except SQLAlchemyError as exc:
        raise StorageError("Unable to access inventory data store") from exc


def seed_inventory(session: Session | None = None) -> int:
    """Insert CONTEXT seed supplies + orders. Stock is net inbound − outbound. Idempotent on sku."""
    from app.database import get_engine, init_inventory_schema

    if session is None:
        init_inventory_schema()
        with Session(get_engine()) as owned:
            return seed_inventory(owned)

    inserted = 0
    try:
        for item in SEED_ROWS:
            existing = session.exec(
                select(MedicalSupply).where(MedicalSupply.sku == item["sku"])
            ).first()
            if existing is not None:
                continue
            supply = MedicalSupply(
                name=item["name"],
                sku=item["sku"],
                threshold=int(item["threshold"]),
                category=str(item.get("category") or DEFAULT_CATEGORY),
                expiry_date=parse_expiry(item.get("expiry_date")),
            )
            session.add(supply)
            session.flush()
            assert supply.id is not None
            created = utc_now()
            clinic_id = str(item.get("clinic_id") or DEFAULT_CLINIC_ID)
            country = str(item.get("country") or DEFAULT_COUNTRY)
            session.add(
                InboundOrder(
                    product_id=supply.id,
                    product_name=supply.name,
                    sku=supply.sku,
                    quantity=int(item["inbound"]),
                    notes=str(item["inbound_notes"]),
                    created_at=created,
                    user_uuid=SEED_USER_UUID,
                    clinic_id=clinic_id,
                    country=country,
                )
            )
            outbound_qty = int(item["outbound"])
            if outbound_qty > 0:
                session.add(
                    OutboundOrder(
                        product_id=supply.id,
                        product_name=supply.name,
                        sku=supply.sku,
                        quantity=outbound_qty,
                        notes=str(item["outbound_notes"]),
                        created_at=created,
                        user_uuid=SEED_USER_UUID,
                        clinic_id=clinic_id,
                        country=country,
                        department=str(item.get("department") or DEFAULT_DEPARTMENT),
                    )
                )
            inserted += 1
        session.commit()
        return inserted
    except SQLAlchemyError as exc:
        session.rollback()
        raise StorageError("Unable to access inventory data store") from exc
