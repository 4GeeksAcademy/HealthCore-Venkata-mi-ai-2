"""Pydantic request/response schemas — not SQLModel ORM classes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OrderType(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class ProductCategory(str, Enum):
    medication = "medication"
    ppe = "ppe"
    consumable = "consumable"
    equipment = "equipment"


class MedicalSupplyCreate(BaseModel):
    name: str
    sku: str
    threshold: int = Field(ge=0)
    category: ProductCategory = ProductCategory.consumable
    expiry_date: str | None = None  # YYYY-MM-DD optional


class MedicalSupplyResponse(BaseModel):
    id: int
    name: str
    sku: str
    threshold: int
    current_stock: int
    category: str = "consumable"
    expiry_date: str | None = None


class InboundOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    notes: str = ""
    clinic_id: str = "us-tx-001"
    country: str = "US"
    total_cost: float | None = None


class OutboundOrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    notes: str = ""
    clinic_id: str = "us-tx-001"
    country: str = "US"
    department: str = "general_consultation"


class InboundOrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    notes: str
    created_at: str
    user_uuid: str
    created_by: str
    sku: str = ""
    clinic_id: str = "us-tx-001"
    country: str = "US"
    product_category: str = "consumable"
    expiry_date: str | None = None
    total_cost: float | None = None


class OutboundOrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    notes: str
    created_at: str
    user_uuid: str
    created_by: str
    sku: str
    threshold: int
    previous_stock: int
    current_stock: int
    threshold_crossed: bool
    clinic_id: str = "us-tx-001"
    country: str = "US"
    department: str = "general_consultation"
    product_category: str = "consumable"
    expiry_date: str | None = None


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
    clinic_id: str = "us-tx-001"
    country: str = "US"
    department: str | None = None
