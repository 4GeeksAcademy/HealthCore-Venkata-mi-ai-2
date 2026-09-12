"""Clinic inventory HTTP routes — SQLModel / Supabase, JWT required."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.database import get_db
from app.deps.auth import get_current_user
from app.inventory.models import InboundOrder, MedicalSupply, OutboundOrder
from app.inventory.schemas import (
    InboundOrderCreate,
    InboundOrderResponse,
    InventoryOrderResponse,
    MedicalSupplyCreate,
    MedicalSupplyResponse,
    OutboundOrderCreate,
    OutboundOrderResponse,
)
from app.inventory.service import (
    current_stock_for,
    get_supply,
    insufficient_stock_detail,
    iso_timestamp,
    list_orders,
    list_supplies,
    utc_now,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _user_uuid(user: dict) -> str:
    return str(user.get("id"))


@router.get("/products", response_model=list[MedicalSupplyResponse])
def get_products(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[MedicalSupplyResponse]:
    return list_supplies(session)


@router.post("/products", response_model=MedicalSupplyResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: MedicalSupplyCreate,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> MedicalSupplyResponse:
    existing = session.exec(select(MedicalSupply).where(MedicalSupply.sku == payload.sku)).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="SKU already exists.")
    row = MedicalSupply(name=payload.name, sku=payload.sku, threshold=payload.threshold)
    session.add(row)
    try:
        session.commit()
        session.refresh(row)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="SKU already exists.")
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again.")
    assert row.id is not None
    return MedicalSupplyResponse(
        id=row.id,
        name=row.name,
        sku=row.sku,
        threshold=row.threshold,
        current_stock=0,
    )


@router.get("/products/{product_id}", response_model=MedicalSupplyResponse)
def get_product(
    product_id: int,
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> MedicalSupplyResponse:
    row = get_supply(session, product_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return row


@router.post(
    "/orders/inbound",
    response_model=InboundOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_inbound(
    payload: InboundOrderCreate,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> InboundOrderResponse:
    product = session.get(MedicalSupply, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    row = InboundOrder(
        product_id=payload.product_id,
        product_name=product.name,
        sku=product.sku,
        quantity=payload.quantity,
        notes=payload.notes,
        created_at=utc_now(),
        user_uuid=_user_uuid(user),
    )
    session.add(row)
    try:
        session.commit()
        session.refresh(row)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again.")
    assert row.id is not None
    return InboundOrderResponse(
        id=row.id,
        product_id=row.product_id,
        product_name=product.name,
        quantity=row.quantity,
        notes=row.notes,
        created_at=iso_timestamp(row.created_at),
        user_uuid=row.user_uuid,
        created_by=str(user.get("email") or row.user_uuid),
    )


@router.post(
    "/orders/outbound",
    response_model=OutboundOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_outbound(
    payload: OutboundOrderCreate,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> OutboundOrderResponse:
    product = session.get(MedicalSupply, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    available = current_stock_for(session, payload.product_id)
    if payload.quantity > available:
        raise HTTPException(
            status_code=400,
            detail=insufficient_stock_detail(available, payload.quantity),
        )
    row = OutboundOrder(
        product_id=payload.product_id,
        product_name=product.name,
        sku=product.sku,
        quantity=payload.quantity,
        notes=payload.notes,
        created_at=utc_now(),
        user_uuid=_user_uuid(user),
    )
    session.add(row)
    try:
        session.commit()
        session.refresh(row)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again.")
    assert row.id is not None
    return OutboundOrderResponse(
        id=row.id,
        product_id=row.product_id,
        product_name=product.name,
        quantity=row.quantity,
        notes=row.notes,
        created_at=iso_timestamp(row.created_at),
        user_uuid=row.user_uuid,
        created_by=str(user.get("email") or row.user_uuid),
    )


@router.get("/orders", response_model=list[InventoryOrderResponse])
def get_orders(
    _: dict = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[InventoryOrderResponse]:
    return list_orders(session)
