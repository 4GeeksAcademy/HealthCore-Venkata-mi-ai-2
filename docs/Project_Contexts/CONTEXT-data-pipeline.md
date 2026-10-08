# CONTEXT: HealthCore Business Performance Data Pipeline

**Audience:** AI coding agents designing, then later implementing, the business-performance pipeline in this monorepo.  
**Parent:** [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md) (telemetry contract: supply events, no PHI, monthly executive use).  
**Design:** [PIPELINE_DESIGN.md](../../data/pipelines/PIPELINE_DESIGN.md).  
**Related:** [telemetry-plan.md](../telemetry/telemetry-plan.md), [CONTEXT-telemetry-storage.md](./CONTEXT-telemetry-storage.md), [Telemetry_technical_report.md](./Telemetry_technical_report.md).  
**Last updated:** 2026-10-05

This file is the company brief for the data-pipeline assignment (Part 1: design). It is not orchestration code.

**Status (2026-10-07):** Part 1 design is locked. Part 2 implementation follows [CONTEXT-resilience-pipeline.md](./CONTEXT-resilience-pipeline.md) and [PIPELINE_DESIGN.md](../../data/pipelines/PIPELINE_DESIGN.md).

---

## 1. Why this exists at HealthCore

HealthCore Digital already stores backoffice telemetry in Supabase `telemetry_events` and serves an engineering report from `GET /telemetry/report` (`services/telemetry/analysis.py`): events per day, error rate by type, API latency per day, and login failure rate.

That report does not answer the business question in section 4 of [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md). Dr. Okonkwo (CEO) and Claire (compliance) need a **Monthly Clinic Supply Performance Report**: supply cost, consumption, stockout frequency, and expiry risk by clinic and country, ready on the first working day of the month. Marcus (clinical operations) uses the stockout and expiry counts from that same pack.

This pipeline exists only to produce that pack. It is a new pipeline. It does not replace the technical report.

---

## 2. Business deliverable

| Item | Lock |
|------|------|
| Name | Monthly Clinic Supply Performance Report |
| Audience | Dr. Okonkwo and Claire. Non-technical. Numbers, not raw events. |
| Cadence | Monthly. The previous UTC month is computed so the pack exists before the first working day. |
| Grain | One row per `clinic_id` per calendar month (`month_start` = first UTC day of that month). |
| Destination | `reporting.monthly_clinic_supply_performance` |
| Unique key | `(clinic_id, month_start)` |

Do not invent another KPI for v1. Do not convert currencies. `US` clinics use `USD`. `UK` clinics use `GBP`. Rows sit side by side. Never add USD and GBP into one total.

---

## 3. KPIs

| KPI | Column | Rule |
|-----|--------|------|
| Supply Cost per Clinic | `total_supply_cost` | Sum of `properties.total_cost` on accepted `inbound_order_created` events in the month. |
| Supply Consumption Volume | `supply_consumption_count` | Count of accepted `outbound_order_created` events in the month. |
| Critical Stockout Frequency | `critical_stockout_count` | Count of accepted `stock_threshold_triggered` events in the month. |
| Expiry Risk Count | `expiry_risk_count` | Count of accepted `supply_expiry_flagged` events in the month. |

`department` is required on `outbound_order_created` so consumption is a clinical area, never a patient. It is not a column on the destination table. The unique key and the KPI query stay clinic + month.

---

## 4. Source

Read `telemetry_events` only. Never write it. Never use it as this pipeline’s destination.

| `event_type` | KPI |
|--------------|-----|
| `inbound_order_created` | Supply Cost per Clinic |
| `outbound_order_created` | Supply Consumption Volume |
| `stock_threshold_triggered` | Critical Stockout Frequency |
| `supply_expiry_flagged` | Expiry Risk Count |

No other event type enters the four numbers. Do not join incident rows, patient tables, or `medical_supply` for v1.

### Envelope already stored

Columns in use: `id`, `timestamp` (timestamptz), `service`, `event_type`, `level`, `value`, `message`, `tags` (JSONB).

`tags` holds `eventId`, `sessionId`, `userId`, `schemaVersion`, `requestId`, and the allowlisted property keys. Dedup key is `tags.eventId`. Fact time is `timestamp`, not the time the pipeline loads the row.

### Properties this pipeline requires

The catalogue in [telemetry-plan.md](../telemetry/telemetry-plan.md) does not yet carry `clinic_id`, `country`, `department`, `total_cost`, or `supply_expiry_flagged`. Part 1 does not add emitters. The extract contract is:

| Event | Required `tags` / properties | Notes |
|-------|------------------------------|-------|
| All four | `eventId`, `clinic_id`, `country` | `country` is `US` or `UK` and must match the clinic id prefix (`us-` / `uk-`). |
| `inbound_order_created` | `total_cost` (numeric, ≥ 0), `product_id`, `product_category`, `quantity` | `total_cost` is an additive field on this existing event. It is the order cost in the clinic currency, not a patient charge. Do not multiply by `quantity`. |
| `outbound_order_created` | `department`, `product_id`, `product_category`, `quantity` | `department` allowlist: `general_consultation`, `chronic_care`, `primary_care`, `specialty_care`, `chronic_disease_management`. |
| `stock_threshold_triggered` | `product_id`, `product_category` | Count the event. Do not recompute the threshold here. |
| `supply_expiry_flagged` | `product_id`, `product_category`, `quantity`, `expiry_date` | Already required by [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md). The emitter owns the “within 30 days” rule. This pipeline counts the event. |

`product_category` is `medication`, `ppe`, `consumable`, or `equipment`.

Rows missing a required field, with an unknown `clinic_id`, or with a country that disagrees with the clinic prefix are excluded from the rollup and counted on the run. Do not guess a clinic, a cost, or a zero.

### Clinic allowlist

Use the distinct `clinic_id` values already in [scripts/samples/incidents-healthcore.csv](../../scripts/samples/incidents-healthcore.csv). Do not copy `patient_id` from that file. Do not invent `austin-north`.

| `clinic_id` | `country` | `currency` |
|-------------|-----------|------------|
| `us-tx-001` | `US` | `USD` |
| `us-tx-002` | `US` | `USD` |
| `us-fl-001` | `US` | `USD` |
| `us-fl-002` | `US` | `USD` |
| `us-ga-001` | `US` | `USD` |
| `us-ga-002` | `US` | `USD` |
| `uk-lon-001` | `UK` | `GBP` |
| `uk-lon-002` | `UK` | `GBP` |
| `uk-man-001` | `UK` | `GBP` |
| `uk-man-002` | `UK` | `GBP` |

A completed month writes one row for every id in this list. A clinic with no accepted events still gets zeros. That is a measured zero, not a missing run.

---

## 5. Destination

```sql
create table reporting.monthly_clinic_supply_performance (
  id uuid primary key default gen_random_uuid(),
  clinic_id text not null,
  country text not null,
  month_start date not null,
  total_supply_cost numeric not null default 0,
  supply_consumption_count integer not null default 0,
  critical_stockout_count integer not null default 0,
  expiry_risk_count integer not null default 0,
  currency text not null,
  computed_at timestamptz not null default now(),
  unique (clinic_id, month_start)
);
```

Idempotent load is `INSERT … ON CONFLICT (clinic_id, month_start) DO UPDATE`.

Execution audit lives in `reporting.pipeline_runs` (see the design). That table is not a substitute for the KPI table.

---

## 6. Routes

New module `services/reporting/`, mounted on the existing FastAPI app. No ETL in the route handlers. Handlers import `data/pipelines/`. `data/pipelines/` does not import `services/`.

| Method | Path | Calls |
|--------|------|--------|
| GET | `/reporting/pipeline-runs/latest` | `latest_pipeline_run` |
| POST | `/reporting/pipeline-runs` | `trigger_monthly_clinic_supply_performance` |
| GET | `/reporting/monthly-clinic-supply-performance` | `query_monthly_clinic_supply_performance` |

`GET /reporting/monthly-clinic-supply-performance` accepts optional `month_start` (default: the latest `month_start` already stored) and returns:

```json
{
  "month_start": "2026-07-01",
  "clinics": [
    {
      "clinic_id": "us-tx-001",
      "country": "US",
      "total_supply_cost": 18420.50,
      "supply_consumption_count": 340,
      "critical_stockout_count": 1,
      "expiry_risk_count": 4,
      "currency": "USD"
    }
  ]
}
```

These routes use the existing bearer JWT. They are not public and they are not part of `uis/healthcore`.

`GET /telemetry/report` stays the engineering report. Do not add these KPIs to it.

---

## 7. Out of scope for Part 1

- Prefect implementation, SQL migrations, and the three routes above (named in the design only).
- Changes to `services/telemetry/analysis.py` or `GET /telemetry/report`.
- Writes to `telemetry_events`, including an ingest upsert on `eventId`.
- New event types other than using `supply_expiry_flagged`, which the telemetry CONTEXT already requires.
- Emitters, backoffice pages, and the public site.
- FX conversion, patient identifiers, order `notes`, staff email, passwords, or reset tokens.
- Rewriting [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md) or prior plan stamps.

---

## 8. Robustness the design must show

- **Idempotency.** A second run of the same month, including a rerun after a failed load, yields the same KPI rows. Dedup is `eventId` at extract. Load upserts `(clinic_id, month_start)`.
- **Observability.** Every run writes `reporting.pipeline_runs`, including a run that loads zeros. No row means the pipeline did not run.
- **Recoverability.** `phase` on the run is the checkpoint. Resume by recomputing the month and upserting. A stale `Running` row must not block the next run forever.
