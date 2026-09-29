# CONTEXT: HealthCore Telemetry — Storage

**Audience:** AI coding agents replacing the telemetry stub with Supabase persistence in this monorepo.  
**Parent:** [CONTEXT.md](../../CONTEXT.md).  
**Contract:** [telemetry-plan.md](../telemetry/telemetry-plan.md) and [event-schemas.json](../telemetry/event-schemas.json) (plan eval **10/10 Pass**).  
**Prerequisite:** [CONTEXT-telemetry-frontend-capture.md](./CONTEXT-telemetry-frontend-capture.md) — backoffice `track()` batches reach `POST /telemetry/events` with **200** (capture eval **12/12 Pass**).  
**Related:** [CONTEXT-telemetry-plan.md](./CONTEXT-telemetry-plan.md), inventory Supabase path via `INVENTORY_BACKEND` / `SUPABASE_DATABASE_URL`.  
**Last updated:** 2026-09-28

This file is the **storage** assignment. Events already flow from the frontend to the stub. The stub validates and discards. This phase creates `telemetry_events` in Supabase and makes `POST /telemetry/events` persist valid events in one bulk insert. **Do not change the frontend.** Do not modify `TelemetryEvent` fields from the capture phase — reuse that model as a per-item validator only.

If batches do not already return **200** from the stub, fix capture first. Do not start storage until that works.

---

## 1. Why this exists at HealthCore

The stub proved the envelope arrives with the correct shape. Ops still cannot query what staff did in inventory or where technical failures happened, because nothing is saved. Persistence turns the same URL into the real sink: validate each event, store the good ones, count the bad ones, return `{ received, stored, rejected }`.

Telemetry is write-only. Events are immutable facts. Do not add UPDATE or DELETE endpoints or repository methods for this table.

Do not instrument or change `uis/healthcore`. Do not share layouts with the backoffice. Do not change `uis/backoffice/lib/telemetry.ts` or any backoffice emitter for this assignment.

---

## 2. HealthCore bindings

Use these. The course README’s generic names and port **8000** do not apply here.

| Topic | Use this |
|-------|----------|
| Endpoint URL | Same as stub: `POST /telemetry/events` on `services/api` (browser via `/hc-api/telemetry/events` → API **8001**) |
| Frontend | **Zero line changes.** `TelemetryService` only needs HTTP **200**; response body may gain `stored` / `rejected` |
| `TelemetryEvent` | Keep `services/api/app/models/telemetry.py` **TelemetryEvent** unchanged (same fields as capture). Do **not** type the request body as `list[TelemetryEvent]` |
| Loose envelope | Accept `{ "events": [ ...raw dicts... ] }` so one invalid item does not produce FastAPI **422** for the whole batch |
| Per-event validation | `TelemetryEvent.model_validate(raw)` inside `try/except ValidationError`; valid → bulk list; invalid → `rejected += 1` |
| Persistence | Supabase Postgres via existing `SUPABASE_DATABASE_URL` (same pooler URI used for inventory when `INVENTORY_BACKEND=supabase`) |
| Table | `telemetry_events` — see Phase 1 columns and indexes |
| `tags` JSONB | Envelope `properties` (allowlist keys only per plan/schemas). Also store analytics envelope fields inside `tags` when required by the plan: `eventId`, `sessionId`, `userId`, `schemaVersion`, `requestId` |
| `service` | Constant `backoffice` for events from this capture path (or derive from envelope if later emitters add API-origin events) |
| Bulk insert | **One** insert/transaction per batch for all valid rows — not one INSERT per event |
| Response | `{ "received": N, "stored": M, "rejected": R }` with HTTP **200** when the envelope has a parseable `events` array |
| Secrets | Do not commit `.env` or plaintext passwords. Prefer encrypted `SUPABASE_DATABASE_URL` (`enc:v1:`) when leaving the machine |

Confirm optional dimensions in `tags` match [telemetry-plan.md](../telemetry/telemetry-plan.md) property allowlists. Document any envelope→`tags` mapping there if not already explicit.

---

## 3. Complementary knowledge (non-negotiable)

### Why bulk insert

`TelemetryService` can flush ~20 events every 10 seconds from many users. One INSERT per event multiplies transactions and exhausts the pool. All valid events in a batch go in **one** bulk insert / single transaction.

### Partial validation (per-event parsing)

| Approach | Mixed batch |
|----------|-------------|
| Typed body `events: list[TelemetryEvent]` | Entire request **422** — nothing stored |
| Loose `{ "events": [...] }` + `model_validate` in a loop | Valid stored; invalid counted in `rejected`; HTTP **200** |

Reuse `TelemetryEvent` as a **per-item** validator. Do not use it as the FastAPI body element type for the full list.

---

## 4. Work order

### Phase 1 — Storage table in Supabase

- [ ] Create `telemetry_events` with:

  | Column | Type | Notes |
  |--------|------|--------|
  | `id` | `uuid` PK, default `gen_random_uuid()` | |
  | `timestamp` | `timestamptz` NOT NULL | From event ISO 8601 |
  | `service` | `text` NOT NULL | e.g. `backoffice` |
  | `event_type` | `text` NOT NULL | `entity_action` |
  | `level` | `text` default `'info'` | `info` / `warn` / `error` |
  | `value` | `numeric` nullable | Optional from properties when defined |
  | `message` | `text` nullable | Optional summary |
  | `tags` | `jsonb` default `'{}'` | `properties` + plan envelope keys |

- [ ] Map API → row:

  | DB column | Source |
  |-----------|--------|
  | `timestamp` | `event.timestamp` |
  | `service` | `backoffice` (or derived) |
  | `event_type` | `event.event_type` |
  | `level` | From event type or default `info` (technical errors → `warn`/`error`) |
  | `value` | Optional numeric from `properties` |
  | `message` | Optional human-readable summary |
  | `tags` | `event.properties` (allowlist) plus envelope ids required by the plan |

- [ ] Indexes: `timestamp`, `event_type`, GIN on `tags`.
- [ ] No UPDATE/DELETE logic for this table.

### Phase 2 — Real FastAPI endpoint

- [ ] Replace stub `POST /telemetry/events` with the real handler (same path).
- [ ] Loose envelope parse; per-event `model_validate`; bulk insert valids; return `{ received, stored, rejected }`.
- [ ] Confirm frontend still works unchanged (status **200** only).

### Phase 3 — End-to-end verification

- [ ] In backoffice: create at least one inbound and one outbound order; produce at least one technical event (e.g. failed login / client error).
- [ ] In Supabase Table Editor / SQL: confirm rows with correct `event_type`, `timestamp`, `tags`.
- [ ] Manually POST a mixed valid/invalid batch; confirm `stored` and `rejected` counts and that valids appear in the table.

---

## 5. What we will evaluate

- [ ] `telemetry_events` exists with the eight columns, three indexes, and no UPDATE/DELETE logic
- [ ] `POST /telemetry/events` bulk-inserts and returns `{ "received", "stored", "rejected" }`
- [ ] Invalid events rejected individually without cancelling the batch (per-event `model_validate`, not typed `list[TelemetryEvent]` body → whole-batch **422**)
- [ ] `TelemetryEvent` Pydantic model unchanged from the previous project — reused as-is
- [ ] Frontend unchanged — stub → real is transparent
- [ ] Events appear with `event_type`, `timestamp`, and `tags` correctly populated (technical and business)
- [ ] Stored `tags` preserve property allowlists and CONTEXT-specific dimensions from `telemetry-plan.md`
- [ ] Insert is a single operation per batch, not one INSERT per event

---

## 6. Explicit non-goals

- Changing `uis/backoffice` telemetry client, emitters, or Next rewrites
- Changing `uis/healthcore`
- Rewriting the approved telemetry plan/schema unless a mapping note for `tags` is required
- CRUD (update/delete) on telemetry rows
- Closing MS5 solely by completing this storage phase

---

## 7. Agent instructions

1. Confirm stub already returns **200** for real backoffice batches before coding storage.
2. Keep `TelemetryEvent` field definitions unchanged; replace `TelemetryBatch` / request typing so the body is not `list[TelemetryEvent]`.
3. Prefer the existing SQLModel/Supabase engine patterns used for inventory when wiring the table and bulk insert; create indexes via migration SQL or startup DDL matching Phase 1.
4. Log counts and `event_type` values only — never log full `properties`, emails, or tokens.
5. After implementation: run the evaluation checklist in §5, show the result to the human, and **wait for explicit “save”** before writing any evaluation Results file.
6. Do not commit `.env` or secrets.
