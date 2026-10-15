# Background Processes Evaluation

**Date:** 2026-10-14 (re-run)  
**Rubric:** BackgroundProcesses “What We Will Evaluate” (ten checks)  
**Implementation as of:** [HC-MS6-PLAN-085](../../plans/HC-MS6-PLAN-085-20261014-background-processes-impl.md)  
**Saved after:** [HC-MS6-PLAN-089](../../plans/HC-MS6-PLAN-089-20261014-background-processes-eval-rerun.md) (same-day overwrite; prior save was PLAN-086)  
**Overall: PASS (10/10)**

| Doc | Path |
|-----|------|
| CONTEXT | [`docs/Project_Contexts/BackgroundProcesses.md`](../../../docs/Project_Contexts/BackgroundProcesses.md) |
| Company | [`CONTEXT-healthcore.md`](../../../CONTEXT-healthcore.md) |
| Script | [`scripts/nightly_export.py`](../../../scripts/nightly_export.py) |
| Status control | [`services/job_runner/`](../../../services/job_runner/) |
| Tests | [`tests/jobs/test_nightly_export.py`](../../../tests/jobs/test_nightly_export.py) |
| Cron docs | [`scripts/README.md`](../../../scripts/README.md) |

Same-day re-eval after human request. Overwrites this single 2026-10-14 Results file only. Does not close MS6. Does not replace pipeline or telemetry evals. CONTEXT-healthcore gap work (PLAN-087/088) did not change the nightly orchestration contract.

## Method (re-run)

- Re-ran `python -m pytest tests/jobs/test_nightly_export.py`: **8 passed**.
- Smoke (isolated SQLite): `TARGET_DATE=2026-10-13 NIGHTLY_SKIP_PIPELINE=1` → completed with CSV write; second run → skipped as duplicate; held `processing` lock → abort exit 0.
- Confirmed script does not import FastAPI `app.main`; cron remains documented as OS crontab `15 2 * * *` UTC in `scripts/README.md`.
- Confirmed `job_runs` remains separate from `reporting.pipeline_runs`.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Script is an independent process (not FastAPI main thread) | **Pass** | CLI `scripts/nightly_export.py`; no FastAPI import/execution on API thread. |
| 2 | State machine + `target_date` on `job_runs` | **Pass** | `pending` → `processing` → `completed` \| `failed` in `services/job_runner/service.py`. |
| 3 | `processing` is the distributed lock | **Pass** | Smoke lock abort + unit test; no separate lock table. |
| 4 | Idempotent per `target_date` | **Pass** | Duplicate skip smoke + tests; CSV skip-if-exists. |
| 5 | Failure never leaves `processing` | **Pass** | `mark_failed` on exception; failure unit test. |
| 6 | CSV in `data/raw/` for target date | **Pass** | Smoke wrote `telemetry_2026-10-13.csv` from `telemetry_events`. |
| 7 | `job_runs` ≠ `pipeline_runs` | **Pass** | Separate package/table; pipeline still owns ETL audit. |
| 8 | Logs include timestamp, job name, status | **Pass** | Smoke lines: UTC `asctime`, `job=nightly_export`, `status=`. |
| 9 | Trigger / cron expression documented | **Pass** | `15 2 * * *` UTC in `scripts/README.md` + script docstring. |
| 10 | `TARGET_DATE` override | **Pass** | Env override in smoke and unit tests. |

## Residuals (do not fail the rubric)

- Host crontab still must be installed by the operator; repo documents the expression.
- Full pipeline subprocess needs reporting/telemetry DB env when `NIGHTLY_SKIP_PIPELINE` is unset.
- Assignment `telemetry_kpi_daily` module remains mapped to `data/pipelines/pipeline.py`.

## Verdict

Ticket **#DEV-53** still meets the official Background Processes rubric after re-check. **PASS (10/10).**
