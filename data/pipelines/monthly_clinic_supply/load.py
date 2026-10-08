"""Idempotent load into reporting.monthly_clinic_supply_performance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .db import get_engine, init_reporting_schema, is_sqlite, kpi_table


def load_monthly_clinic_supply_performance(
    rows: list[dict[str, Any]],
    engine: Engine | None = None,
) -> int:
    eng = engine or get_engine()
    init_reporting_schema(eng)
    table = kpi_table(eng)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    loaded = 0
    try:
        with eng.begin() as conn:
            for row in rows:
                row_id = str(uuid4())
                computed_at = now.isoformat() if is_sqlite(eng) else now
                if is_sqlite(eng):
                    conn.execute(
                        text(
                            f"""
                            INSERT INTO {table} (
                              id, clinic_id, country, month_start,
                              total_supply_cost, supply_consumption_count,
                              critical_stockout_count, expiry_risk_count,
                              currency, computed_at
                            ) VALUES (
                              :id, :clinic_id, :country, :month_start,
                              :total_supply_cost, :supply_consumption_count,
                              :critical_stockout_count, :expiry_risk_count,
                              :currency, :computed_at
                            )
                            ON CONFLICT(clinic_id, month_start) DO UPDATE SET
                              country = excluded.country,
                              total_supply_cost = excluded.total_supply_cost,
                              supply_consumption_count = excluded.supply_consumption_count,
                              critical_stockout_count = excluded.critical_stockout_count,
                              expiry_risk_count = excluded.expiry_risk_count,
                              currency = excluded.currency,
                              computed_at = excluded.computed_at
                            """
                        ),
                        {
                            "id": row_id,
                            "clinic_id": row["clinic_id"],
                            "country": row["country"],
                            "month_start": row["month_start"],
                            "total_supply_cost": row["total_supply_cost"],
                            "supply_consumption_count": row["supply_consumption_count"],
                            "critical_stockout_count": row["critical_stockout_count"],
                            "expiry_risk_count": row["expiry_risk_count"],
                            "currency": row["currency"],
                            "computed_at": computed_at,
                        },
                    )
                else:
                    conn.execute(
                        text(
                            f"""
                            INSERT INTO {table} (
                              clinic_id, country, month_start,
                              total_supply_cost, supply_consumption_count,
                              critical_stockout_count, expiry_risk_count,
                              currency, computed_at
                            ) VALUES (
                              :clinic_id, :country, :month_start,
                              :total_supply_cost, :supply_consumption_count,
                              :critical_stockout_count, :expiry_risk_count,
                              :currency, :computed_at
                            )
                            ON CONFLICT (clinic_id, month_start) DO UPDATE SET
                              country = EXCLUDED.country,
                              total_supply_cost = EXCLUDED.total_supply_cost,
                              supply_consumption_count = EXCLUDED.supply_consumption_count,
                              critical_stockout_count = EXCLUDED.critical_stockout_count,
                              expiry_risk_count = EXCLUDED.expiry_risk_count,
                              currency = EXCLUDED.currency,
                              computed_at = EXCLUDED.computed_at
                            """
                        ),
                        {
                            "clinic_id": row["clinic_id"],
                            "country": row["country"],
                            "month_start": row["month_start"],
                            "total_supply_cost": row["total_supply_cost"],
                            "supply_consumption_count": row["supply_consumption_count"],
                            "critical_stockout_count": row["critical_stockout_count"],
                            "expiry_risk_count": row["expiry_risk_count"],
                            "currency": row["currency"],
                            "computed_at": computed_at,
                        },
                    )
                loaded += 1
    except SQLAlchemyError as exc:
        raise RuntimeError(f"supabase_timeout:{exc.__class__.__name__}") from exc
    return loaded
