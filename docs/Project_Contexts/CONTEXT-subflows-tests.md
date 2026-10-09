# CONTEXT: HealthCore Pipeline Subflows, Tests, and Dashboard

**Audience:** AI coding agents implementing Part 3 of the data-pipeline series.  
**Parent:** [CONTEXT-healthcore.md](../../CONTEXT-healthcore.md).  
**KPI contract:** [CONTEXT-data-pipeline.md](./CONTEXT-data-pipeline.md).  
**Part 2:** [CONTEXT-resilience-pipeline.md](./CONTEXT-resilience-pipeline.md).  
**Design:** [PIPELINE_DESIGN.md](../../data/pipelines/PIPELINE_DESIGN.md).  
**Assignment:** Subflows and Tests (Part 3 of 3).  
**Last updated:** 2026-10-09

This file is the implementation brief for production hardening of the Monthly Clinic Supply Performance pipeline. It does not replace Parts 1–2.

**Status (2026-10-09):** Implementation. Do not change `services/telemetry/analysis.py` or write into `telemetry_events`.

---

## 1. Deliverable

Same pack as Part 2 — **Monthly Clinic Supply Performance Report** for Dr. Okonkwo and Claire:

| KPI (label on dashboard) | Column |
|--------------------------|--------|
| Supply Cost per Clinic | `total_supply_cost` |
| Supply Consumption Volume | `supply_consumption_count` |
| Critical Stockout Frequency | `critical_stockout_count` |
| Expiry Risk Count | `expiry_risk_count` |

Cadence: **monthly** (`month_start`). Destination table and KPI query endpoint unchanged from Part 2.

---

## 2. Part 3 work order

### Phase 1 — Subflows

Main flow `monthly_clinic_supply_performance` (CLI entry remains [`data/pipelines/pipeline.py`](../../data/pipelines/pipeline.py)) must invoke **at least three** `@flow` subflows with explicit inputs/outputs:

| Subflow | Role |
|---------|------|
| `extract_clinic_supply_telemetry` | Read `telemetry_events` (Option A fixture fallback) |
| `transform_monthly_clinic_supply_kpis` | Build clinic-month KPI rows |
| `load_monthly_clinic_supply_performance` | Upsert destination table |
| `snapshot_monthly_clinic_supply_eval` | Optional; invoke with `return_state=True` |

Names must stay HealthCore / design vocabulary — not generic `extract_data`.

### Phase 2 — Unit tests

- Path: [`tests/pipelines/test_pipeline.py`](../../tests/pipelines/test_pipeline.py)
- At least three transformation tests (the four KPIs)
- In-memory fixtures only — no live DB
- At least one defensive / malformed-input test
- At least one hand-calculated KPI assertion
- Run: `python -m pytest tests/pipelines/test_pipeline.py`

Pure KPI logic lives under [`data/process/`](../../data/process/) so tests do not need Prefect or SQL.

### Phase 3 — CLI

`python data/pipelines/pipeline.py` must still complete after the subflow refactor.

### Phase 4 — Dashboard

Authenticated backoffice page [`uis/backoffice/app/(internal)/reporting/page.tsx`](../../uis/backoffice/app/(internal)/reporting/page.tsx) at `/reporting`:

- Fetches `GET /reporting/monthly-clinic-supply-performance` via `/hc-api`
- Shows all four KPI labels from §1 and the month period
- Readable for Dr. Okonkwo / Claire (not an engineering debug page)

---

## 3. Out of scope

- Changes to `services/telemetry/analysis.py` or `GET /telemetry/report`
- Writes to `telemetry_events`
- Public site `uis/healthcore`
- Closing MS5
- Inventing enhancements not already in the design (optional: document concurrency lock already shipped for Part 1 Q10)
