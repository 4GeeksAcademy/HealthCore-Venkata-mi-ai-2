"""Inventory domain helpers: computed stock, seed, order mapping."""

from __future__ import annotations

from datetime import datetime, timezone

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

SEED_ROWS: list[dict] = [
    {
        "name": "Nitrile exam gloves (box of 100)",
        "sku": "HC-PPE-GLV-100",
        "threshold": 24,
        "inbound": 40,
        "outbound": 28,
        "inbound_notes": "McKesson delivery — Austin clinic restock",
        "outbound_notes": "Manchester clinic weekly consumption",
    },
    {
        "name": "Alcohol prep pads (box of 200)",
        "sku": "HC-CLN-PAD-200",
        "threshold": 30,
        "inbound": 80,
        "outbound": 0,
        "inbound_notes": "Clinic restock",
        "outbound_notes": "",
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


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
    return MedicalSupplyResponse(
        id=row.id,
        name=row.name,
        sku=row.sku,
        threshold=row.threshold,
        current_stock=stock,
    )


def to_order_response(
    row: InboundOrder | OutboundOrder,
    order_type: OrderType,
) -> InventoryOrderResponse:
    assert row.id is not None
    product_name = row.product_name or (row.product.name if row.product is not None else "")
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
            )
            session.add(supply)
            session.flush()
            assert supply.id is not None
            created = utc_now()
            session.add(
                InboundOrder(
                    product_id=supply.id,
                    product_name=supply.name,
                    sku=supply.sku,
                    quantity=int(item["inbound"]),
                    notes=str(item["inbound_notes"]),
                    created_at=created,
                    user_uuid=SEED_USER_UUID,
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
                    )
                )
            inserted += 1
        session.commit()
        return inserted
    except SQLAlchemyError as exc:
        session.rollback()
        raise StorageError("Unable to access inventory data store") from exc
