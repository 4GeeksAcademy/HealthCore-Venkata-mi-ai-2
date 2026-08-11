"""Pydantic models for the HealthCore Supplier Directory."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SupplierStatus(str, Enum):
    active = "active"
    suspended = "suspended"


class Country(str, Enum):
    US = "US"
    UK = "UK"


class ProductCategory(str, Enum):
    MEDICAL_SUPPLIES = "MEDICAL_SUPPLIES"
    LAB_CONSUMABLES = "LAB_CONSUMABLES"
    PPE = "PPE"
    PHARMACEUTICALS = "PHARMACEUTICALS"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    FACILITIES = "FACILITIES"
    DIAGNOSTIC_EQUIPMENT = "DIAGNOSTIC_EQUIPMENT"


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    country: Country
    product_categories: list[ProductCategory] = Field(min_length=1)
    contract_rate: float = Field(gt=0)
    status: SupplierStatus


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: Country
    product_categories: list[ProductCategory]
    contract_rate: float = Field(gt=0)
    updated_at: str
    status: SupplierStatus


class RateUpdate(BaseModel):
    contract_rate: float = Field(gt=0)


class StatusUpdate(BaseModel):
    status: SupplierStatus


class DeleteAck(BaseModel):
    ok: bool = True
    id: int
