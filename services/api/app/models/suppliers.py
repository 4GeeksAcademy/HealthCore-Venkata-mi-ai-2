"""Pydantic models for the HealthCore Supplier Directory."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SupplierStatus(str, Enum):
    active = "active"
    suspended = "suspended"


class Country(str, Enum):
    USA = "USA"
    UK = "UK"


class Currency(str, Enum):
    USD = "USD"
    GBP = "GBP"


class ProductCategory(str, Enum):
    MEDICAL_SUPPLIES = "MEDICAL_SUPPLIES"
    LAB_CONSUMABLES = "LAB_CONSUMABLES"
    PPE = "PPE"
    PHARMACEUTICALS = "PHARMACEUTICALS"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    FACILITIES = "FACILITIES"
    DIAGNOSTIC_EQUIPMENT = "DIAGNOSTIC_EQUIPMENT"


COUNTRY_CURRENCY: dict[Country, Currency] = {
    Country.USA: Currency.USD,
    Country.UK: Currency.GBP,
}


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    country: Country
    categories: list[ProductCategory] = Field(min_length=1)
    monthly_rate: float = Field(gt=0)
    currency: Currency
    status: SupplierStatus

    @model_validator(mode="after")
    def currency_matches_country(self) -> SupplierCreate:
        expected = COUNTRY_CURRENCY[self.country]
        if self.currency != expected:
            raise ValueError(
                f"currency must be {expected.value} when country is {self.country.value}"
            )
        return self


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: Country
    categories: list[ProductCategory]
    monthly_rate: float = Field(gt=0)
    currency: Currency
    updated_at: str
    status: SupplierStatus


class RateUpdate(BaseModel):
    monthly_rate: float = Field(gt=0)


class StatusUpdate(BaseModel):
    status: SupplierStatus


class DeleteAck(BaseModel):
    ok: bool = True
    id: int
