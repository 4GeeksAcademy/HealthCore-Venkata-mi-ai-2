# Telemetry Storage Evaluation

**Date:** 2026-09-28  
**Rubric:** “What We Will Evaluate” (eight storage checks)  
**Implementation as of:** [HC-MS5-PLAN-071](../../plans/HC-MS5-PLAN-071-20260928-telemetry-storage.md)  
**Saved after:** [HC-MS5-PLAN-072](../../plans/HC-MS5-PLAN-072-20260928-telemetry-storage-eval.md)  
**Overall: PASS (8/8)**

| Doc | Path |
|-----|------|
| CONTEXT | [`docs/Project_Contexts/CONTEXT-telemetry-storage.md`](../../../docs/Project_Contexts/CONTEXT-telemetry-storage.md) |
| Plan mapping | [`docs/telemetry/telemetry-plan.md`](../../../docs/telemetry/telemetry-plan.md) |
| Sink | [`services/api/app/routers/telemetry.py`](../../../services/api/app/routers/telemetry.py) |
| Store | [`services/api/app/telemetry/store.py`](../../../services/api/app/telemetry/store.py) |
| Envelope | [`services/api/app/models/telemetry.py`](../../../services/api/app/models/telemetry.py) |

Saved after human confirmation of the chat scorecard. This evaluation does not close or reopen MS5. It does not replace [TelemetryCapture-20260925.md](./TelemetryCapture-20260925.md) or [TelemetryPlan-20260923.md](./TelemetryPlan-20260923.md).

## Method

- Confirmed Supabase `telemetry_events` columns and indexes (`timestamp`, `event_type`, GIN on `tags` as `jsonb`).
- Confirmed no UPDATE/DELETE helpers on the telemetry store (insert-only bulk path).
- Posted a mixed valid/invalid batch to `http://127.0.0.1:8001/telemetry/events` → **200** `{"received":4,"stored":2,"rejected":2}`.
- Queried stored rows for `inbound_order_created` and `login_failed` with `event_type`, `timestamp`, and `tags` (allowlist keys + envelope ids).
- Confirmed `TelemetryEvent` field definitions unchanged; batch body is loose `list[Any]` with per-item `model_validate`.
- Confirmed no `uis/` diffs for this phase.
- Pytest API suite **61 passed**.

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `telemetry_events` exists with eight columns, three indexes, no UPDATE/DELETE | **Pass** | Columns `id`, `timestamp`, `service`, `event_type`, `level`, `value`, `message`, `tags`. Indexes `ix_telemetry_events_timestamp`, `ix_telemetry_events_event_type`, `ix_telemetry_events_tags_gin`. Store is insert-only. |
| 2 | `POST /telemetry/events` bulk-inserts and returns `{ received, stored, rejected }` | **Pass** | Live response `{"received":4,"stored":2,"rejected":2}`. `bulk_insert_events` uses one `session.add_all` + `commit`. |
| 3 | Invalid events rejected individually without cancelling the batch | **Pass** | Loose `TelemetryBatchEnvelope`; per-event `TelemetryEvent.model_validate`. Mixed batch HTTP **200**, not whole-batch **422**. |
| 4 | `TelemetryEvent` Pydantic model unchanged from capture phase | **Pass** | Same fields: `eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`. |
| 5 | Frontend unchanged — stub → real is transparent | **Pass** | No `uis/` diffs. Same URL; HTTP **200** only required by `TelemetryService`. |
| 6 | Events appear with `event_type`, `timestamp`, and `tags` (technical and business) | **Pass** | Supabase rows for `inbound_order_created` and `login_failed` with populated `tags`. |
| 7 | Stored `tags` preserve allowlists and plan envelope dimensions | **Pass** | `properties` keys plus `eventId`, `sessionId`, `userId`, `schemaVersion`, `requestId` per `telemetry-plan.md` mapping. |
| 8 | Insert is a single operation per batch | **Pass** | One transaction via `session.add_all(rows)` then `commit`. |

## Residuals

None.

## Verdict

Stub replaced with Supabase bulk persistence and per-event validation. Frontend unchanged. **PASS (8/8).**
