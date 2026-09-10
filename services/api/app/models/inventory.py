"""Pydantic models for HealthCore clinic inventory."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OrderType(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    stock: int
    threshold: int


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    notes: str = ""


class OrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    type: OrderType
    notes: str
    created_at: str
    created_by: str
