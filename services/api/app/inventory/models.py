"""SQLModel ORM tables for HealthCore medical-supply inventory (Supabase)."""

from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class MedicalSupply(SQLModel, table=True):
    __tablename__ = "medical_supply"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(index=True, unique=True)
    threshold: int


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
    product: MedicalSupply | None = Relationship()
