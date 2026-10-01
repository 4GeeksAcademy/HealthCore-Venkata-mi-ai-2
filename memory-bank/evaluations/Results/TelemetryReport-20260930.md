# Telemetry Technical Report Evaluation

**Date:** 2026-09-30  
**Rubric:** “What We Will Evaluate” (ten technical-report checks)  
**Implementation as of:** [HC-MS5-PLAN-073](../../plans/HC-MS5-PLAN-073-20260930-telemetry-technical-report.md)  
**Saved after:** [HC-MS5-PLAN-074](../../plans/HC-MS5-PLAN-074-20260930-telemetry-report-eval.md)  
**Overall: PASS (10/10)**

| Doc | Path |
|-----|------|
| Brief | [`docs/Project_Contexts/Telemetry_technical_report.md`](../../../docs/Project_Contexts/Telemetry_technical_report.md) |
| Company | [`CONTEXT-healthcore.md`](../../../CONTEXT-healthcore.md) |
| Analysis | [`services/telemetry/analysis.py`](../../../services/telemetry/analysis.py) |
| Endpoint | [`services/api/app/routers/telemetry.py`](../../../services/api/app/routers/telemetry.py) |
| Page | [`uis/backoffice/app/(internal)/telemetry/page.tsx`](../../../uis/backoffice/app/(internal)/telemetry/page.tsx) |

Saved after human confirmation of the chat scorecard. This evaluation does not close or reopen MS5. It does not replace the plan, capture, or storage evals.

## Method

- Read `services/telemetry/analysis.py` for SQL window filters, `pd.to_datetime(..., utc=True)`, and Pandas `groupby` / `agg`.
- Pytest `tests/test_telemetry.py`: grouped metrics, 60-second cache (second call does not rerun `events_per_day`), and a rejected inverted date window. API suite **64 passed**.
- Live `GET http://127.0.0.1:8001/telemetry/report` returned a 7-day period (`2026-09-24` to `2026-10-01`) with `events_per_day` (11 rows), `error_rate_by_type` (10), `latency_per_day` (1), and `auth_failure_rate` (2).
- Supabase `telemetry_events` count was **48**, including `login_failed`, `api_request_failed`, and `api_latency_recorded`.
- Backoffice `http://127.0.0.1:3001/telemetry` returned **200** with the Telemetry report heading and nav link.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `services/telemetry/analysis.py` has at least three independent metric functions | **Pass** | `events_per_day`, `error_rate_by_type`, `latency_per_day`, plus `auth_failure_rate`. |
| 2 | Each function follows load (SQL) → refine (Pandas) → convert types → group → aggregate | **Pass** | Timestamp and `event_type` filters are in SQL. Tags and flags are built in Pandas before `groupby`. |
| 3 | Timestamps converted with `utc=True` before temporal `groupby` | **Pass** | `_prepare` sets `timestamp` with `pd.to_datetime(..., utc=True)` and derives `date` before grouping. |
| 4 | No loops calculate metrics | **Pass** | Aggregates use `groupby`, `size`, `agg`, and `mean`. |
| 5 | Each function returns a JSON list of dicts | **Pass** | `_records` uses `to_json(orient="records")`. |
| 6 | `GET /telemetry/report` accepts optional dates and defaults to 7 days | **Pass** | Omitted params produced a 7-day UTC window. Inverted window returned **422**. |
| 7 | JSON shape is `{ "period", "metrics" }` | **Pass** | Live body included `period.from`, `period.to`, and the four metric keys. |
| 8 | In-memory cache with a 60-second TTL | **Pass** | `report_cache` TTL is 60 seconds. Pytest showed one pipeline call for two identical requests. |
| 9 | Metrics answer technical questions, not business questions | **Pass** | Volume, error rate, API latency, and login failure rate. No revenue or purchasing KPIs. |
| 10 | Metrics have a grouping dimension | **Pass** | Grouped by day and/or `event_type`, not a single global number. |

## Residuals

None.

## Verdict

Operational report is served from stored HealthCore events with a cached endpoint and a backoffice page. **PASS (10/10).**
