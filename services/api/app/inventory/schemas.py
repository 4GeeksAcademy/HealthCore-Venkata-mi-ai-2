"""Pydantic request/response schemas — not SQLModel ORM classes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OrderType(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class MedicalSupplyCreate(BaseModel):
    name: str
    sku: str
    threshold: int = Field(ge=0)


class MedicalSupplyResponse(BaseModel):
    id: int
    name: str
    sku: str
    threshold: int
    current_stock: int


class InboundOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    notes: str = ""


class OutboundOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    notes: str = ""


class InboundOrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    notes: str
    created_at: str
    user_uuid: str
    created_by: str


class OutboundOrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    notes: str
    created_at: str
    user_uuid: str
    created_by: str


class InventoryOrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    type: OrderType
    notes: str
    created_at: str
    user_uuid: str
    created_by: str
