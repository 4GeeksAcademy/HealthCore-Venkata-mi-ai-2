"""Supplier directory HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.suppliers import (
    DeleteAck,
    RateUpdate,
    StatusUpdate,
    SupplierCreate,
    SupplierResponse,
)
from app.deps.auth import get_current_user
from app import suppliers_store as store

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_supplier(
    payload: SupplierCreate,
    _: dict = Depends(get_current_user),
) -> SupplierResponse:
    return store.create_supplier(payload)


@router.get("", response_model=list[SupplierResponse])
@router.get("/", response_model=list[SupplierResponse], include_in_schema=False)
def list_suppliers(
    country: str | None = Query(default=None),
    category: str | None = Query(default=None),
    _: dict = Depends(get_current_user),
) -> list[SupplierResponse]:
    return store.list_suppliers(country=country, category=category)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, _: dict = Depends(get_current_user)) -> SupplierResponse:
    found = store.get_supplier(supplier_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return found


@router.patch("/{supplier_id}/rate", response_model=SupplierResponse)
def patch_rate(
    supplier_id: int,
    payload: RateUpdate,
    _: dict = Depends(get_current_user),
) -> SupplierResponse:
    updated = store.update_rate(supplier_id, payload.monthly_rate)
    if updated is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return updated


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
def patch_status(
    supplier_id: int,
    payload: StatusUpdate,
    _: dict = Depends(get_current_user),
) -> SupplierResponse:
    updated = store.update_status(supplier_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return updated


@router.delete("/{supplier_id}", response_model=DeleteAck)
def delete_supplier(supplier_id: int, _: dict = Depends(get_current_user)) -> DeleteAck:
    removed = store.delete_supplier(supplier_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return DeleteAck(ok=True, id=supplier_id)
