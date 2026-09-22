"""Bulk synthetic rows so timing logs show cache value (CONTEXT seeds stay small)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select
from tinydb import Query

from app.core.errors import StorageError
from app.database import get_engine, init_inventory_schema
from app.inventory.models import InboundOrder, MedicalSupply, OutboundOrder
from app.inventory.service import SEED_USER_UUID, utc_now
from app.models.suppliers import ProductCategory
from app import suppliers_store as store

LOAD_VENDOR_PREFIX = "Load Clinic Vendor"
LOAD_SKU_PREFIX = "HC-LOAD-"

CLINICS = ("Austin", "Miami", "Atlanta", "London", "Manchester")
CATEGORIES = [item.value for item in ProductCategory]
SUPPLY_NAMES = (
    "Nitrile exam gloves",
    "Alcohol prep pads",
    "Face masks",
    "Saline flush syringes",
    "Sharps containers",
    "ECG electrodes",
    "Specimen bags",
    "Hand sanitizer",
)


def seed_supplier_load(count: int = 200) -> int:
    """Insert extra TinyDB vendors. Idempotent on Load Clinic Vendor NNN names."""
    if count < 1:
        return 0
    db = store.get_db()
    try:
        Supplier = Query()
        inserted = 0
        now = store.utc_now_iso()
        for index in range(1, count + 1):
            name = f"{LOAD_VENDOR_PREFIX} {index:03d}"
            if db.search(Supplier.name == name):
                continue
            country = "USA" if index % 2 else "UK"
            category = CATEGORIES[index % len(CATEGORIES)]
            extra = CATEGORIES[(index + 3) % len(CATEGORIES)]
            categories = [category] if extra == category else [category, extra]
            db.insert(
                {
                    "name": name,
                    "country": country,
                    "categories": categories,
                    "monthly_rate": 1200.0 + (index * 37.5),
                    "currency": "USD" if country == "USA" else "GBP",
                    "updated_at": now,
                    "status": "active" if index % 7 else "suspended",
                }
            )
            inserted += 1
        return inserted
    except (OSError, ValueError) as exc:
        raise StorageError("Unable to access supplier data store") from exc
    finally:
        db.close()


def seed_inventory_load(
    product_count: int = 40,
    inbound_per_product: int = 20,
    outbound_per_product: int = 12,
    session: Session | None = None,
) -> int:
    """Insert extra supplies + many orders so stock aggregation is measurable."""
    if product_count < 1:
        return 0
    if session is None:
        init_inventory_schema()
        with Session(get_engine()) as owned:
            return seed_inventory_load(
                product_count=product_count,
                inbound_per_product=inbound_per_product,
                outbound_per_product=outbound_per_product,
                session=owned,
            )

    inserted = 0
    try:
        for index in range(1, product_count + 1):
            sku = f"{LOAD_SKU_PREFIX}{index:03d}"
            existing = session.exec(
                select(MedicalSupply).where(MedicalSupply.sku == sku)
            ).first()
            if existing is not None:
                continue
            clinic = CLINICS[index % len(CLINICS)]
            label = SUPPLY_NAMES[index % len(SUPPLY_NAMES)]
            supply = MedicalSupply(
                name=f"{label} ({clinic} clinic pack {index:03d})",
                sku=sku,
                threshold=10 + (index % 20),
            )
            session.add(supply)
            session.flush()
            assert supply.id is not None
            base = utc_now()
            for inbound_n in range(inbound_per_product):
                session.add(
                    InboundOrder(
                        product_id=supply.id,
                        product_name=supply.name,
                        sku=supply.sku,
                        quantity=4 + ((index + inbound_n) % 8),
                        notes=f"{clinic} restock wave {inbound_n + 1}",
                        created_at=base - timedelta(days=(inbound_n % 80) + 1),
                        user_uuid=SEED_USER_UUID,
                    )
                )
            for outbound_n in range(outbound_per_product):
                session.add(
                    OutboundOrder(
                        product_id=supply.id,
                        product_name=supply.name,
                        sku=supply.sku,
                        quantity=1 + ((index + outbound_n) % 3),
                        notes=f"{clinic} weekly consumption {outbound_n + 1}",
                        created_at=base - timedelta(hours=outbound_n + 1),
                        user_uuid=SEED_USER_UUID,
                    )
                )
            inserted += 1
        session.commit()
        return inserted
    except SQLAlchemyError as exc:
        session.rollback()
        raise StorageError("Unable to access inventory data store") from exc
