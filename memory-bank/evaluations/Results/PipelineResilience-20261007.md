# Business Performance Pipeline Resilience Evaluation

**Date:** 2026-10-07  
**Rubric:** ResiliencePipeline (Part 2) “What We Will Evaluate” (fourteen checks)  
**Implementation as of:** [HC-MS5-PLAN-079](../../plans/HC-MS5-PLAN-079-20261007-resilience-pipeline-impl.md)  
**Saved after:** [HC-MS5-PLAN-080](../../plans/HC-MS5-PLAN-080-20261007-resilience-pipeline-eval.md)  
**Overall: PASS (14/14)**

| Doc | Path |
|-----|------|
| CONTEXT | [`docs/Project_Contexts/CONTEXT-resilience-pipeline.md`](../../../docs/Project_Contexts/CONTEXT-resilience-pipeline.md) |
| KPI contract | [`docs/Project_Contexts/CONTEXT-data-pipeline.md`](../../../docs/Project_Contexts/CONTEXT-data-pipeline.md) |
| Design | [`data/pipelines/PIPELINE_DESIGN.md`](../../../data/pipelines/PIPELINE_DESIGN.md) |
| CLI entry | [`data/pipelines/pipeline.py`](../../../data/pipelines/pipeline.py) |

Saved after human confirmation of the chat scorecard. This evaluation does not close or reopen MS5. It does not replace the Part 1 design eval or the telemetry plan, capture, storage, or technical-report evals.

## Method

- Ran `python data/pipelines/pipeline.py --month-start 2026-09-01` twice (Option A fixture when live telemetry had no accepted clinic-tagged rows).
- Confirmed second run used Cached transform and still loaded **10** clinic rows (upsert idempotency).
- Queried KPI rows for `us-tx-001` and `uk-lon-001` against the four CONTEXT KPIs.
- Ran `pytest tests/test_reporting.py tests/test_telemetry.py` from `services/api`: **9 passed**.
- Confirmed `services/telemetry/analysis.py` and `GET /telemetry/report` were not modified for this work.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `data/pipelines/pipeline.py` exists and defines at least one flow with three or more tasks | **Pass** | Flow `monthly_clinic_supply_performance` with `extract_supply_events`, `transform_monthly_clinic_kpis`, `load_monthly_clinic_supply_performance`, plus optional `write_eval_snapshot`. |
| 2 | At least one task has `retries` > 0 and a justification comment | **Pass** | Extract and load use `retries=3`, `retry_delay_seconds=5` with comments on pooler/transient DB failures. |
| 3 | Optional task invoked with `return_state=True`; flow continues on failure | **Pass** | `write_eval_snapshot(..., return_state=True)`; failure is logged and ETL still Completes. |
| 4 | Transformation caching with `cache_key_fn` and `cache_expiration` | **Pass** | Transform uses `task_input_hash` and one-hour expiration; second CLI run reported Cached. |
| 5 | Idempotent load; second run does not duplicate CONTEXT destination rows | **Pass** | `ON CONFLICT (clinic_id, month_start) DO UPDATE`; both runs loaded 10 clinics. |
| 6 | Each run records at least five metadata fields | **Pass** | `pipeline_runs` stores start, end, records extracted/loaded, status, errors (plus phase, source, and more). |
| 7 | `python data/pipelines/pipeline.py` runs the full ETL without errors | **Pass** | Completed with `status=Completed`, `records_loaded=10`, Option A source when needed. |
| 8 | Run command documented | **Pass** | Documented in `PIPELINE_DESIGN.md` and the `pipeline.py` module docstring. |
| 9 | Writes CONTEXT destination table; telemetry report path untouched | **Pass** | KPI table `reporting.monthly_clinic_supply_performance` (local SQLite file when no reporting URI). No writes to `telemetry_events`; engineering report unchanged. |
| 10 | Endpoint returns last pipeline run metadata | **Pass** | `GET /reporting/pipeline-runs/latest` via `latest_pipeline_run`. |
| 11 | Endpoint triggers a manual flow run, importing from `data/pipelines/` | **Pass** | `POST /reporting/pipeline-runs` → `trigger_monthly_clinic_supply_performance`. |
| 12 | Endpoint returns KPI rows from the CONTEXT destination table | **Pass** | `GET /reporting/monthly-clinic-supply-performance` → `query_monthly_clinic_supply_performance`. |
| 13 | KPI values match CONTEXT “KPIs to Measure” | **Pass** | Supply cost, consumption count, stockout count, expiry count from the four mandatory supply events; USD/GBP not summed. |
| 14 | Implementation consistent with `PIPELINE_DESIGN.md` | **Pass** | Flow/task names, upsert key, run lock, Option A fixture, and three reporting routes match the design. |

## Residuals (do not fail the rubric)

- Live `telemetry_events` still often lacks `clinic_id` / `total_cost` / `supply_expiry_flagged`; Option A fixture supplies accepted rows for CLI and tests until emitters are extended later.
- Default reporting destination for local CLI is gitignored `data/process/reporting.db` unless `REPORTING_DATABASE_URL` is set.
- Prefect temporary-server SSL telemetry noise on Windows does not fail the flow.

## Verdict

The resilient Prefect pipeline produces the Monthly Clinic Supply Performance Report with retries, transform caching, an optional non-critical snapshot, idempotent load, CLI execution, and three JWT reporting endpoints, without changing the engineering telemetry report. **PASS (14/14).**
