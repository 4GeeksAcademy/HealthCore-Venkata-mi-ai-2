# Business Performance Pipeline Subflows and Tests Evaluation

**Date:** 2026-10-09  
**Rubric:** Subflows and Tests (Part 3) “What We Will Evaluate” (twelve checks)  
**Implementation as of:** [HC-MS5-PLAN-082](../../plans/HC-MS5-PLAN-082-20261009-subflows-tests-impl.md)  
**Saved after:** [HC-MS5-PLAN-083](../../plans/HC-MS5-PLAN-083-20261009-subflows-tests-eval.md)  
**Overall: PASS (12/12)**

| Doc | Path |
|-----|------|
| CONTEXT | [`docs/Project_Contexts/CONTEXT-subflows-tests.md`](../../../docs/Project_Contexts/CONTEXT-subflows-tests.md) |
| KPI contract | [`docs/Project_Contexts/CONTEXT-data-pipeline.md`](../../../docs/Project_Contexts/CONTEXT-data-pipeline.md) |
| Company | [`CONTEXT-healthcore.md`](../../../CONTEXT-healthcore.md) |
| Design | [`data/pipelines/PIPELINE_DESIGN.md`](../../../data/pipelines/PIPELINE_DESIGN.md) |
| CLI / main flow | [`data/pipelines/pipeline.py`](../../../data/pipelines/pipeline.py) |
| Tests | [`tests/pipelines/test_pipeline.py`](../../../tests/pipelines/test_pipeline.py) |
| Dashboard | [`uis/backoffice/app/(internal)/reporting/page.tsx`](../../../uis/backoffice/app/(internal)/reporting/page.tsx) |

Saved after human confirmation of the chat scorecard. This evaluation does not close or reopen MS5. It does not replace the Part 1 design eval, Part 2 resilience eval, or the telemetry evals.

## Method

- Confirmed main `@flow` `monthly_clinic_supply_performance` in `data/pipelines/pipeline.py` invokes four domain-named `@flow` subflows with explicit inputs/outputs.
- Ran `python -m pytest tests/pipelines/test_pipeline.py`: **8 passed** (in-memory fixtures only).
- Ran `python data/pipelines/pipeline.py --month-start 2026-09-01`: **Completed**, `records_loaded=10`, subflows extract → transform → load → optional snapshot.
- Confirmed backoffice `/reporting` labels the four CONTEXT KPIs and fetches `GET /reporting/monthly-clinic-supply-performance`.
- Confirmed this work did not modify `services/telemetry/analysis.py` or write into `telemetry_events`.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Main flow in `data/pipelines/pipeline.py` invokes at least three `@flow` subflows | **Pass** | Calls `extract_clinic_supply_telemetry`, `transform_monthly_clinic_supply_kpis`, `load_monthly_clinic_supply_performance`, plus optional `snapshot_monthly_clinic_supply_eval`. |
| 2 | Each subflow has explicit inputs/outputs and can run independently | **Pass** | Defined in `monthly_clinic_supply/subflows.py` with typed args and return values; no globals between stages. |
| 3 | `tests/pipelines/test_pipeline.py` exists with ≥3 transform unit tests | **Pass** | Tests for Supply Cost, Consumption Volume, Critical Stockout Frequency, Expiry Risk Count. |
| 4 | Unit tests isolated: in-memory fixtures, no live DB/APIs | **Pass** | Pure helpers in `data/process/clinic_supply_kpis.py` plus `accept_event` checks; no SQL. |
| 5 | ≥1 test for defensive behaviour on invalid input | **Pass** | Rejects inbound without `total_cost`; skips non-numeric cost; tolerates non-list events. |
| 6 | ≥1 test validates a KPI against CONTEXT definition (hand-calculated) | **Pass** | `us-tx-001` 2026-09: cost 125.50, consumption 2, stockouts 1, expiry 0; allowlist zeros for quiet clinics. |
| 7 | `python -m pytest tests/pipelines/test_pipeline.py` passes | **Pass** | **8 passed**. |
| 8 | CLI still runs full ETL after subflow refactor | **Pass** | `python data/pipelines/pipeline.py --month-start 2026-09-01` → Completed, 10 clinics. |
| 9 | Names use domain / KPI vocabulary from CONTEXT | **Pass** | Subflow, task, and test names reference clinic supply KPIs — not generic `extract_data`. |
| 10 | `telemetry_events` and `services/telemetry/analysis.py` unmodified for this refactor | **Pass** | KPI path uses reporting destination and Option A fixture; engineering report untouched. |
| 11 | Backoffice dashboard shows every CONTEXT KPI from the reporting endpoint | **Pass** | `/reporting` tables for all four KPIs via JWT `GET /reporting/monthly-clinic-supply-performance`. |
| 12 | Dashboard legible to a non-technical stakeholder | **Pass** | Labeled for Dr. Okonkwo / Claire with month period; plain-language section copy. |

## Residuals (do not fail the rubric)

- Live `telemetry_events` may still lack clinic-tagged supply properties; Option A fixture covers CLI when needed.
- Design question 10 (concurrency lock) was already implemented in Part 2; noted in `PIPELINE_DESIGN.md` — no duplicate lock added in Part 3.
- Prefect temporary-server SSL telemetry noise on Windows does not fail the flow.

## Verdict

The Monthly Clinic Supply Performance pipeline is production-shaped for Part 3: domain-named subflows, isolated KPI unit tests, preserved CLI entry, and a leadership-readable backoffice dashboard, without changing the engineering telemetry report. **PASS (12/12).**
