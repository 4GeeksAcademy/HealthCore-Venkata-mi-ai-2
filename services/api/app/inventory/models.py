"""SQLModel ORM tables for HealthCore medical-supply inventory (Supabase)."""

from datetime import date, datetime

from sqlmodel import Field, Relationship, SQLModel


class MedicalSupply(SQLModel, table=True):
    __tablename__ = "medical_supply"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(index=True, unique=True)
    threshold: int
    # CONTEXT-healthcore: category + expiry (additive; defaults keep old rows valid)
    category: str = Field(default="consumable")
    expiry_date: date | None = Field(default=None)


class InboundOrder(SQLModel, table=True):
    __tablename__ = "inbound_order"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="medical_supply.id")
    product_name: str = ""
    sku: str = ""
    quantity: int
    notes: str = ""
    created_at: datetime
    user_uuid: str
    clinic_id: str = "us-tx-001"
    country: str = "US"
    product: MedicalSupply | None = Relationship()


class OutboundOrder(SQLModel, table=True):
    __tablename__ = "outbound_order"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="medical_supply.id")
    product_name: str = ""
    sku: str = ""
    quantity: int
    notes: str = ""
    created_at: datetime
    user_uuid: str
    clinic_id: str = "us-tx-001"
    country: str = "US"
    department: str = "general_consultation"
    product: MedicalSupply | None = Relationship()
