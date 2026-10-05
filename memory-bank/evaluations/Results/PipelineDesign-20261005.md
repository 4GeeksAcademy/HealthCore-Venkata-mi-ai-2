# Business Performance Pipeline Design Evaluation

**Date:** 2026-10-05  
**Rubric:** DataPipelinePart1 “What We Will Evaluate” (twelve design checks)  
**Design as of:** [HC-MS5-PLAN-076](../../plans/HC-MS5-PLAN-076-20261005-pipeline-design.md)  
**Saved after:** [HC-MS5-PLAN-077](../../plans/HC-MS5-PLAN-077-20261005-pipeline-design-eval.md)  
**Overall: PASS (12/12)**

| Doc | Path |
|-----|------|
| CONTEXT | [`docs/Project_Contexts/CONTEXT-data-pipeline.md`](../../../docs/Project_Contexts/CONTEXT-data-pipeline.md) |
| Design | [`data/pipelines/PIPELINE_DESIGN.md`](../../../data/pipelines/PIPELINE_DESIGN.md) |

Saved after human confirmation of the chat scorecard. This evaluation does not close or reopen MS5. No Prefect code, destination tables, or reporting routes were part of this score. It does not replace the telemetry plan, capture, storage, or technical-report evals.

## Method

- Read `PIPELINE_DESIGN.md` against the twelve checks in DataPipelinePart1.
- Checked the purpose sentence, destination table name, and four KPIs against `CONTEXT-data-pipeline.md` and the telemetry contract in `CONTEXT-healthcore.md`.
- Confirmed the design does not instruct a change to `services/telemetry/analysis.py` or `GET /telemetry/report`, and does not write into `telemetry_events`.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `data/pipelines/PIPELINE_DESIGN.md` exists and is readable Markdown | **Pass** | Design file is present, with phases, tables, and a Mermaid flow. |
| 2 | Current State section plus the business gap | **Pass** | Phase 1 — Current State. `GET /telemetry/report` answers volume, errors, latency, and login failures. It does not answer clinic supply cost, consumption, stockouts, or expiry. |
| 3 | Extraction format is specified | **Pass** | Phase 2. Source `telemetry_events`. SQL filter on the four `event_type` values and a UTC month window. Payload is columns plus `tags` (`eventId`, `clinic_id`, `country`, `total_cost`, and the event-specific properties). |
| 4 | Purpose is one sentence naming the deliverable and the company KPIs | **Pass** | Opening sentence names the Monthly Clinic Supply Performance Report for Dr. Okonkwo and Claire and the four KPIs: Supply Cost per Clinic, Supply Consumption Volume, Critical Stockout Frequency, Expiry Risk Count. |
| 5 | Technical report is unchanged; output is not stored in `telemetry_events` | **Pass** | Phase 1 and Phase 5 leave `services/telemetry/analysis.py` and `GET /telemetry/report` alone. Output is `reporting.monthly_clinic_supply_performance`, queried through `services/reporting/`. Additive `total_cost` on `inbound_order_created` is specified, not implemented. |
| 6 | Data flow shows extract, transform, and load with real names | **Pass** | Phase 2 diagram: `telemetry_events` → `extract_supply_events` → `transform_monthly_clinic_kpis` → `load_monthly_clinic_supply_performance` → `reporting.monthly_clinic_supply_performance`. |
| 7 | Updates to existing records use a concrete mechanism | **Pass** | `INSERT … ON CONFLICT (clinic_id, month_start) DO UPDATE`. Duplicate source facts collapse on `tags.eventId` before the upsert. |
| 8 | Idempotency describes the second run after a load failure | **Pass** | Phase 3. A partial clinic-month load is not finished by inserting the remainder. The next run recomputes the month and upserts, matching a clean run of the same window. |
| 9 | Execution log has at least five fields with name, type, and reason | **Pass** | `reporting.pipeline_runs` table. Includes `run_id` uuid, `started_at` timestamptz, `ended_at` timestamptz, `status` text, `records_extracted` integer, `records_loaded` integer, `phase` text, `error_message` text, each with an audit reason. |
| 10 | Prefect mapping has one main flow and three tasks | **Pass** | Flow `monthly_clinic_supply_performance`. Tasks `extract_supply_events`, `transform_monthly_clinic_kpis`, `load_monthly_clinic_supply_performance`. States Running, Completed, Failed. Supabase URI is a Prefect block, not a committed secret. |
| 11 | Three `services/reporting/` endpoints name the `data/pipelines/` functions they import | **Pass** | `GET /reporting/pipeline-runs/latest` → `latest_pipeline_run`. `POST /reporting/pipeline-runs` → `trigger_monthly_clinic_supply_performance`. `GET /reporting/monthly-clinic-supply-performance` → `query_monthly_clinic_supply_performance`. |
| 12 | Design matches the company telemetry metrics | **Pass** | The four source events are the supply metrics in `CONTEXT-healthcore.md`, including `supply_expiry_flagged`, with `clinic_id` and `country`. The design states that the current catalogue does not emit those fields yet and does not guess missing values. |

## Residuals (do not fail the rubric)

- No Prefect flows, SQL migrations, emitters, or `services/reporting/` routes. This score is the design only.
- The clinic allowlist is the ten distinct ids in `scripts/samples/incidents-healthcore.csv`, not a twelfth invented clinic.

## Verdict

The design produces the Monthly Clinic Supply Performance Report from the four supply events, keeps the engineering telemetry report separate, and specifies idempotent load, an audit log, Prefect tasks, and the three reporting routes. **PASS (12/12).**
