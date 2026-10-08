# CONTEXT: HealthCore Resilient Business Performance Pipeline

**Audience:** AI coding agents implementing Part 2 of the data-pipeline series.  
**Parent:** [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md).  
**KPI contract:** [CONTEXT-data-pipeline.md](./CONTEXT-data-pipeline.md).  
**Design:** [PIPELINE_DESIGN.md](../../data/pipelines/PIPELINE_DESIGN.md).  
**Assignment:** ResiliencePipeline (Part 2 of 3).  
**Last updated:** 2026-10-07

This file is the implementation brief for the resilient Prefect pipeline. It does not replace Part 1.

**Status (2026-10-07):** Implementation. Follow this file and the approved design. Do not change `services/telemetry/analysis.py` or `GET /telemetry/report`. Do not write into `telemetry_events`.

---

## 1. Deliverable

Produce the **Monthly Clinic Supply Performance Report** for Dr. Okonkwo and Claire:

| KPI | Column | Source `event_type` |
|-----|--------|---------------------|
| Supply Cost per Clinic | `total_supply_cost` | `inbound_order_created` (`tags.total_cost`) |
| Supply Consumption Volume | `supply_consumption_count` | `outbound_order_created` |
| Critical Stockout Frequency | `critical_stockout_count` | `stock_threshold_triggered` |
| Expiry Risk Count | `expiry_risk_count` | `supply_expiry_flagged` |

Destination: `reporting.monthly_clinic_supply_performance` (unique `(clinic_id, month_start)`).  
Run audit: `reporting.pipeline_runs`.  
Clinic ids: the ten ids in [CONTEXT-data-pipeline.md](./CONTEXT-data-pipeline.md). Currency `USD`/`GBP` with no FX conversion. No PHI.

---

## 2. Source strategy (Option A)

1. Read `telemetry_events` (read-only) for the UTC month.
2. Accept only rows with the required tags from the data-pipeline CONTEXT.
3. If the month has **no accepted rows** after filter/dedup, load synthetic events from [`data/raw/monthly_clinic_supply_events.json`](../../data/raw/monthly_clinic_supply_events.json) for that month so the CLI and upsert path still run.
4. Never write back to `telemetry_events`. Never join incident rows or copy `patient_id`.

---

## 3. Prefect names (must match the design)

| Kind | Name |
|------|------|
| Flow | `monthly_clinic_supply_performance` |
| Task | `extract_supply_events` |
| Task | `transform_monthly_clinic_kpis` |
| Task | `load_monthly_clinic_supply_performance` |
| Optional task | `write_eval_snapshot` (non-critical; `return_state=True`) |

CLI entry: [`data/pipelines/pipeline.py`](../../data/pipelines/pipeline.py).

Schedule: **06:00 UTC on the 1st** of each month for the **previous** UTC month. Manual runs may pass `month_start`.

---

## 4. Resilience requirements

- Retries + `retry_delay_seconds` on every task that talks to the database; justify the count in a comment.
- At least one optional task invoked with `return_state=True` so its failure does not stop extract → transform → load.
- Caching on the transform task: `cache_key_fn` + `cache_expiration` (one hour); comment what the key is.
- Idempotent load: `ON CONFLICT (clinic_id, month_start) DO UPDATE`.
- Each run records at least start, end, records processed, status, and errors in `reporting.pipeline_runs`.

---

## 5. Endpoints

Module [`services/reporting/`](../../services/reporting/), mounted on the FastAPI app. JWT required. Handlers import from `data/pipelines/` only.

| Method | Path |
|--------|------|
| GET | `/reporting/pipeline-runs/latest` |
| POST | `/reporting/pipeline-runs` |
| GET | `/reporting/monthly-clinic-supply-performance` |

KPI response shape matches [CONTEXT-data-pipeline.md](./CONTEXT-data-pipeline.md) §6.

---

## 6. Out of scope

- Changes to the engineering telemetry report path.
- Emitter / catalogue rewrites (except using the Option A fixture).
- Public site `uis/healthcore`.
- Closing MS5.
- Rewriting prior plan stamps or [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md).
