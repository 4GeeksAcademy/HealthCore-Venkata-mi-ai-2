"""Inventory persistence switch: TinyDB JSON or SQLModel (Supabase / SQLite)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.errors import StorageError
from app.database import get_engine, init_inventory_schema
from app.inventory import service as sql_service
from app.inventory.models import InboundOrder, MedicalSupply, OutboundOrder
from app.inventory.schemas import (
    InboundOrderResponse,
    InventoryOrderResponse,
    MedicalSupplyResponse,
    OutboundOrderResponse,
)
from app import inventory_store as tiny_store


def uses_tinydb() -> bool:
    return get_settings().inventory_backend.strip().lower() == "tinydb"


def uses_supabase() -> bool:
    return get_settings().inventory_backend.strip().lower() == "supabase"


def inventory_sql_url() -> str:
    """SQLAlchemy URL for supabase mode (encrypted Supabase URI preferred)."""
    settings = get_settings()
    if settings.supabase_database_url:
        return settings.supabase_database_url
    return settings.database_url


def list_products() -> list[MedicalSupplyResponse]:
    if uses_tinydb():
        return tiny_store.list_products()
    with Session(get_engine()) as session:
        return sql_service.list_supplies(session)


def get_product(product_id: int) -> MedicalSupplyResponse | None:
    if uses_tinydb():
        return tiny_store.get_product(product_id)
    with Session(get_engine()) as session:
        return sql_service.get_supply(session, product_id)


def create_product(
    *,
    name: str,
    sku: str,
    threshold: int,
    category: str = sql_service.DEFAULT_CATEGORY,
    expiry_date: str | None = None,
) -> MedicalSupplyResponse:
    if uses_tinydb():
        try:
            return tiny_store.create_product(
                name=name,
                sku=sku,
                threshold=threshold,
                category=category,
                expiry_date=expiry_date,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    with Session(get_engine()) as session:
        existing = session.exec(select(MedicalSupply).where(MedicalSupply.sku == sku)).first()
        if existing is not None:
            raise HTTPException(status_code=400, detail="SKU already exists.")
        try:
            parsed_expiry = sql_service.parse_expiry(expiry_date)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="expiry_date must be YYYY-MM-DD") from exc
        row = MedicalSupply(
            name=name,
            sku=sku,
            threshold=threshold,
            category=category or sql_service.DEFAULT_CATEGORY,
            expiry_date=parsed_expiry,
        )
        session.add(row)
        try:
            session.commit()
            session.refresh(row)
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=400, detail="SKU already exists.")
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(
                status_code=503, detail="Service temporarily unavailable. Please try again."
            ) from exc
        assert row.id is not None
        return sql_service.to_supply_response(row, 0)


def create_inbound(
    *,
    product_id: int,
    quantity: int,
    notes: str,
    user_uuid: str,
    user_email: str,
    clinic_id: str = sql_service.DEFAULT_CLINIC_ID,
    country: str = sql_service.DEFAULT_COUNTRY,
    total_cost: float | None = None,
) -> InboundOrderResponse:
    if uses_tinydb():
        try:
            return tiny_store.create_inbound(
                product_id=product_id,
                quantity=quantity,
                notes=notes,
                user_uuid=user_uuid,
                user_email=user_email,
                clinic_id=clinic_id,
                country=country,
                total_cost=total_cost,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    with Session(get_engine()) as session:
        product = session.get(MedicalSupply, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found.")
        row = InboundOrder(
            product_id=product_id,
            product_name=product.name,
            sku=product.sku,
            quantity=quantity,
            notes=notes,
            created_at=sql_service.utc_now(),
            user_uuid=user_uuid,
            clinic_id=clinic_id or sql_service.DEFAULT_CLINIC_ID,
            country=country or sql_service.DEFAULT_COUNTRY,
        )
        session.add(row)
        try:
            session.commit()
            session.refresh(row)
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(
                status_code=503, detail="Service temporarily unavailable. Please try again."
            ) from exc
        assert row.id is not None
        return InboundOrderResponse(
            id=row.id,
            product_id=row.product_id,
            product_name=product.name,
            quantity=row.quantity,
            notes=row.notes,
            created_at=sql_service.iso_timestamp(row.created_at),
            user_uuid=row.user_uuid,
            created_by=user_email or user_uuid,
            sku=product.sku,
            clinic_id=row.clinic_id,
            country=row.country,
            product_category=getattr(product, "category", None) or sql_service.DEFAULT_CATEGORY,
            expiry_date=sql_service.format_expiry(getattr(product, "expiry_date", None)),
            total_cost=total_cost,
        )


def create_outbound(
    *,
    product_id: int,
    quantity: int,
    notes: str,
    user_uuid: str,
    user_email: str,
    clinic_id: str = sql_service.DEFAULT_CLINIC_ID,
    country: str = sql_service.DEFAULT_COUNTRY,
    department: str = sql_service.DEFAULT_DEPARTMENT,
) -> OutboundOrderResponse:
    if uses_tinydb():
        try:
            return tiny_store.create_outbound(
                product_id=product_id,
                quantity=quantity,
                notes=notes,
                user_uuid=user_uuid,
                user_email=user_email,
                clinic_id=clinic_id,
                country=country,
                department=department,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    with Session(get_engine()) as session:
        product = session.get(MedicalSupply, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found.")
        previous_stock = sql_service.current_stock_for(session, product_id)
        if quantity > previous_stock:
            raise HTTPException(
                status_code=400,
                detail=sql_service.insufficient_stock_detail(previous_stock, quantity),
            )
        row = OutboundOrder(
            product_id=product_id,
            product_name=product.name,
            sku=product.sku,
            quantity=quantity,
            notes=notes,
            created_at=sql_service.utc_now(),
            user_uuid=user_uuid,
            clinic_id=clinic_id or sql_service.DEFAULT_CLINIC_ID,
            country=country or sql_service.DEFAULT_COUNTRY,
            department=department or sql_service.DEFAULT_DEPARTMENT,
        )
        session.add(row)
        try:
            session.commit()
            session.refresh(row)
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(
                status_code=503, detail="Service temporarily unavailable. Please try again."
            ) from exc
        assert row.id is not None
        current_stock = sql_service.current_stock_for(session, product_id)
        return OutboundOrderResponse(
            id=row.id,
            product_id=row.product_id,
            product_name=product.name,
            quantity=row.quantity,
            notes=row.notes,
            created_at=sql_service.iso_timestamp(row.created_at),
            user_uuid=row.user_uuid,
            created_by=user_email or user_uuid,
            sku=product.sku,
            threshold=product.threshold,
            previous_stock=previous_stock,
            current_stock=current_stock,
            threshold_crossed=sql_service.threshold_crossed(
                previous_stock, current_stock, product.threshold
            ),
            clinic_id=row.clinic_id,
            country=row.country,
            department=row.department,
            product_category=getattr(product, "category", None) or sql_service.DEFAULT_CATEGORY,
            expiry_date=sql_service.format_expiry(getattr(product, "expiry_date", None)),
        )


def list_orders() -> list[InventoryOrderResponse]:
    if uses_tinydb():
        return tiny_store.list_orders()
    with Session(get_engine()) as session:
        return sql_service.list_orders(session)


def seed_inventory() -> int:
    if uses_tinydb():
        tiny_store.init_store()
        return tiny_store.seed_inventory()
    init_inventory_schema()
    return sql_service.seed_inventory()


def init_inventory_backend() -> None:
    """Prepare the active inventory store on API startup."""
    backend = get_settings().inventory_backend.strip().lower()
    if backend not in {"tinydb", "supabase"}:
        raise StorageError("INVENTORY_BACKEND must be tinydb or supabase")
    if backend == "tinydb":
        tiny_store.init_store()
        return
    if not inventory_sql_url():
        raise StorageError(
            "SUPABASE_DATABASE_URL or DATABASE_URL is required when INVENTORY_BACKEND=supabase"
        )
    init_inventory_schema()
