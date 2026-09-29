"""Clinic inventory HTTP routes — TinyDB or Supabase via inventory.repo."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.core.response_cache import (
    PRODUCTS_KEY,
    PRODUCTS_TTL_SECONDS,
    invalidate_products,
    read_cached_rows,
    store_cached_rows,
)
from app.deps.auth import get_current_user
from app.inventory import repo as inventory_repo
from app.inventory.schemas import (
    InboundOrderCreate,
    InboundOrderResponse,
    InventoryOrderResponse,
    MedicalSupplyCreate,
    MedicalSupplyResponse,
    OutboundOrderCreate,
    OutboundOrderResponse,
)
from app.inventory.service import DIRECT_STOCK_EDIT_DETAIL

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _user_uuid(user: dict) -> str:
    return str(user.get("id"))


@router.get("/products", response_model=list[MedicalSupplyResponse])
def get_products(
    response: Response,
    _: dict = Depends(get_current_user),
) -> list[MedicalSupplyResponse]:
    cached = read_cached_rows(response, PRODUCTS_KEY)
    if cached is not None:
        return [MedicalSupplyResponse.model_validate(row) for row in cached]
    rows = inventory_repo.list_products()
    store_cached_rows(
        PRODUCTS_KEY,
        [row.model_dump(mode="json") for row in rows],
        PRODUCTS_TTL_SECONDS,
    )
    return rows


@router.post("/products", response_model=MedicalSupplyResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: Request,
    _: dict = Depends(get_current_user),
) -> MedicalSupplyResponse:
    try:
        raw = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Request body must be a JSON object.")
    if not isinstance(raw, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object.")
    if "stock" in raw or "current_stock" in raw:
        raise HTTPException(status_code=400, detail=DIRECT_STOCK_EDIT_DETAIL)
    try:
        payload = MedicalSupplyCreate.model_validate(raw)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors())
    created = inventory_repo.create_product(
        name=payload.name, sku=payload.sku, threshold=payload.threshold
    )
    invalidate_products()
    return created


@router.get("/products/{product_id}", response_model=MedicalSupplyResponse)
def get_product(
    product_id: int,
    _: dict = Depends(get_current_user),
) -> MedicalSupplyResponse:
    row = inventory_repo.get_product(product_id)
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
) -> InboundOrderResponse:
    created = inventory_repo.create_inbound(
        product_id=payload.product_id,
        quantity=payload.quantity,
        notes=payload.notes,
        user_uuid=_user_uuid(user),
        user_email=str(user.get("email") or ""),
    )
    invalidate_products()
    return created


@router.post(
    "/orders/outbound",
    response_model=OutboundOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_outbound(
    payload: OutboundOrderCreate,
    user: dict = Depends(get_current_user),
) -> OutboundOrderResponse:
    created = inventory_repo.create_outbound(
        product_id=payload.product_id,
        quantity=payload.quantity,
        notes=payload.notes,
        user_uuid=_user_uuid(user),
        user_email=str(user.get("email") or ""),
    )
    invalidate_products()
    return created


@router.get("/orders", response_model=list[InventoryOrderResponse])
def get_orders(
    _: dict = Depends(get_current_user),
) -> list[InventoryOrderResponse]:
    return inventory_repo.list_orders()
