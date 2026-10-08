"""Read KPI rows for GET /reporting/monthly-clinic-supply-performance."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .db import get_engine, init_reporting_schema, is_sqlite, kpi_table
from .flow import parse_month_start


def query_monthly_clinic_supply_performance(
    month_start: str | date | None = None,
    engine: Engine | None = None,
) -> dict[str, Any]:
    eng = engine or get_engine()
    init_reporting_schema(eng)
    table = kpi_table(eng)
    sqlite = is_sqlite(eng)

    try:
        with eng.connect() as conn:
            if month_start is None:
                latest = conn.execute(
                    text(f"SELECT month_start FROM {table} ORDER BY month_start DESC LIMIT 1")
                ).first()
                if latest is None:
                    target = parse_month_start(None)
                else:
                    value = latest[0]
                    target = date.fromisoformat(str(value)[:10])
            else:
                target = parse_month_start(month_start)

            result = conn.execute(
                text(
                    f"""
                    SELECT clinic_id, country, total_supply_cost,
                           supply_consumption_count, critical_stockout_count,
                           expiry_risk_count, currency
                    FROM {table}
                    WHERE month_start = :month_start
                    ORDER BY clinic_id
                    """
                ),
                {"month_start": target.isoformat() if sqlite else target},
            )
            clinics = []
            for row in result.mappings():
                clinics.append(
                    {
                        "clinic_id": row["clinic_id"],
                        "country": row["country"],
                        "total_supply_cost": float(row["total_supply_cost"]),
                        "supply_consumption_count": int(row["supply_consumption_count"]),
                        "critical_stockout_count": int(row["critical_stockout_count"]),
                        "expiry_risk_count": int(row["expiry_risk_count"]),
                        "currency": row["currency"],
                    }
                )
    except SQLAlchemyError as exc:
        raise RuntimeError("Unable to read monthly clinic supply performance") from exc

    return {"month_start": target.isoformat(), "clinics": clinics}
