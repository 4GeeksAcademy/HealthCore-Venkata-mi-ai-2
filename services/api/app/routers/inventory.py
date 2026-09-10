"""Clinic inventory HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import get_current_user
from app.inventory_store import create_order, list_orders, list_products
from app.models.inventory import OrderCreate, OrderResponse, OrderType, ProductResponse

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _staff_email(user: dict) -> str:
    return str(user.get("email") or "unknown@healthcore.example")


@router.get("/products", response_model=list[ProductResponse])
def get_products(_: dict = Depends(get_current_user)) -> list[ProductResponse]:
    return list_products()


@router.post("/inbound", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def post_inbound(
    payload: OrderCreate,
    user: dict = Depends(get_current_user),
) -> OrderResponse:
    order, error = create_order(
        product_id=payload.product_id,
        quantity=payload.quantity,
        notes=payload.notes,
        order_type=OrderType.inbound,
        created_by=_staff_email(user),
    )
    if error == "Product not found.":
        raise HTTPException(status_code=404, detail=error)
    if error:
        raise HTTPException(status_code=400, detail=error)
    assert order is not None
    return order


@router.post("/outbound", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def post_outbound(
    payload: OrderCreate,
    user: dict = Depends(get_current_user),
) -> OrderResponse:
    order, error = create_order(
        product_id=payload.product_id,
        quantity=payload.quantity,
        notes=payload.notes,
        order_type=OrderType.outbound,
        created_by=_staff_email(user),
    )
    if error == "Product not found.":
        raise HTTPException(status_code=404, detail=error)
    if error:
        raise HTTPException(status_code=400, detail=error)
    assert order is not None
    return order


@router.get("/orders", response_model=list[OrderResponse])
def get_orders(_: dict = Depends(get_current_user)) -> list[OrderResponse]:
    return list_orders()
