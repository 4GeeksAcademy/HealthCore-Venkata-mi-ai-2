# CONTEXT: HealthCore Telemetry — Frontend Capture

**Audience:** AI coding agents implementing backoffice telemetry capture in this monorepo.  
**Parent:** [CONTEXT.md](../../CONTEXT.md).  
**Contract:** [telemetry-plan.md](../telemetry/telemetry-plan.md) and [event-schemas.json](../telemetry/event-schemas.json) (eval **10/10 Pass**).  
**Related:** [CONTEXT-telemetry-plan.md](./CONTEXT-telemetry-plan.md).  
**Last updated:** 2026-09-25

This file is the capture assignment. It does not add emitters. The next session implements stub, then service, then instrumentation. Do not rewrite the approved plan or schema unless a new `event_type` is required for Web Vitals, and then update both files together.

---

## 1. Why this exists at HealthCore

The telemetry plan is approved. Staff still cannot see events, because nothing in `uis/backoffice` calls `track()` and the API has no receiver. This phase captures events in the backoffice, queues them, and posts batches to a stub. The stub checks the envelope and returns 200. It does not store events. Persistence is a later phase.

Do not instrument `uis/healthcore`. Do not share layouts with the backoffice.

---

## 2. HealthCore bindings

Use these. The course README’s generic names and port **8000** do not apply here.

| Topic | Use this |
|-------|----------|
| Frontend service | `uis/backoffice/lib/telemetry.ts`. There is no `uis/backoffice/src/services/`. Do not create that tree. |
| Public API | `track(eventType: string, properties: Record<string, unknown>): void` only. `eventType` becomes `event_type`. |
| Envelope | Filled inside `track()`. Callers do not pass `eventId`, `sessionId`, `userId`, `timestamp`, `schemaVersion`, or `requestId`. |
| `userId` | `String(AuthMe.id)` from `uis/backoffice/lib/auth-api.ts` (TinyDB id, JWT `sub`). Never email, name, phone, or password. `null` when no session exists (`login_failed`, `password_reset_failed`). |
| `sessionId` | Created at a successful login. Kept in tab memory. Not `localStorage`. Not an email. |
| `schemaVersion` | Constant `1.0.0`. |
| `timestamp` | ISO 8601 UTC at capture time, not at flush time. |
| Stub | `POST /telemetry/events` on the existing app in `services/api`. Include the router from `services/api/app/main.py`. |
| Browser URL | `NEXT_PUBLIC_TELEMETRY_ENDPOINT`. Local value: `http://localhost:3001/hc-api/telemetry/events`. The rewrite in `uis/backoffice/next.config.ts` sends `/hc-api/*` to the API. Same origin so `sendBeacon` is not blocked. |
| API listen port | **8001**, not 8000. |
| Backend setting | Add `TELEMETRY_ENDPOINT` on `Settings` in `services/api/app/core/config.py`. The stub does not redirect with it. The name must exist. |
| Secrets | Do not commit `.env` or `.env.local`. |

`track()` is the only telemetry HTTP client. No other `fetch` or `axios` call may post events.

---

## 3. Work order

1. **Stub.** `POST /telemetry/events` accepts `{ "events": [TelemetryEvent, ...] }`. Log the count and each `event_type` only. Do not log `properties`, emails, or tokens. Return `200` with `{ "received": N }` from a Pydantic response model. `TelemetryEvent` has `eventId`, `timestamp`, `sessionId`, `userId` (string or null), `event_type`, `schemaVersion`, `requestId`, and `properties` (object). Do not write to TinyDB, SQLite, or Supabase. This model is kept for the later persistence phase.
2. **Service.** In-memory queue. POST the batch `{ "events": [...] }` to `NEXT_PUBLIC_TELEMETRY_ENDPOINT` every 10 seconds or at 20 events, whichever comes first. On `visibilitychange` to `hidden`, flush with `navigator.sendBeacon`. If send fails, retry up to 3 times with exponential wait, then drop the batch. Telemetry must not block the UI.
3. **Instrumentation.** After the service exists. Every mandatory event below, then the technical baseline, then as many other planned events as fit. Property keys must match `event-schemas.json`. No extra keys.

---

## 4. Events to instrument

Names and allowlists are in the approved plan. Do not copy the course README’s `network_error` reason or a generic `page_view` name.

**Mandatory (all of them):**

| `event_type` | When |
|--------------|------|
| `inbound_order_created` | `POST /inventory/orders/inbound` returns 201 |
| `outbound_order_created` | `POST /inventory/orders/outbound` returns 201. Include `threshold_crossed` from that body. |
| `order_validation_failed` | Inventory 422, duplicate SKU 400, unknown product 404, or insufficient stock 400. `reason` is `validation_error`, `duplicate_sku`, `product_not_found`, or `insufficient_stock`. Never `notes`. |
| `direct_stock_edit_rejected` | Product create returns 400 `Stock cannot be modified directly. Register an inbound or outbound order.` Properties: `route` `POST /inventory/products`, `rejected_fields` only. No stock number. |
| `stock_threshold_triggered` | Same outbound 201 when `threshold_crossed` is true. Live before/after totals. Not the stock-page color chip. |
| `login_failed` | `POST /auth/login` returns 401. `reason` is `invalid_credentials` or `inactive_user`. `userId` is null. |
| `section_viewed` | Backoffice path from the plan allowlist, as a template (`/hiring/candidates/[id]`, not the raw id). |
| `flow_abandoned` | Inbound, outbound, register, or password reset left without the success response. |

**Technical baseline (required, still plan names):**

- `frontend_error_captured` from a backoffice error boundary and/or `window.onerror` / `unhandledrejection`. Properties: `error_name` and `path` only. Drop message and stack. There is no `error.tsx` today.
- `section_viewed` on the main shell paths (`/`, `/ops`, `/incidents`, `/suppliers`, `/inventory`, `/hiring`).
- At least one of `page_load_recorded` or `api_latency_recorded`.

**Auth capture site:** `uis/backoffice/lib/auth-api.ts` or `LoginForm`, not each page. `login()` today throws a sanitized message from `publicFetch`, so read the 401 `detail` before that sanitization. Map `Invalid credentials` to `invalid_credentials` and `Inactive user` to `inactive_user`. Do not put the typed email or password on the event. `session_expired` is a separate event (`token_expired`, `token_invalid`, `token_missing`). Do not fold it into `login_failed`.

**Also instrument from the plan when the hook is already in the flow you touch:** `product_created`, `login_succeeded` (`role` only), `flow_started`, `password_reset_failed`, `password_change_failed`. Supplier and incident events follow the same allowlists if those screens are wired in this pass. Breadth across categories beats more fields on one event.

---

## 5. Web Vitals

The additional activity asks for Web Vitals on a route. `event-schemas.json` has no Web Vitals `event_type`. Do not invent one in a `track()` call.

`page_load_recorded` is the in-plan load event. Its allowlist is only `path`, `duration_ms`, and `load_kind` (`navigate` or `reload`). Do not add LCP, INP, or CLS to that object.

To emit LCP, INP, or CLS, add one new `event_type` to both the plan and the schema in the same change, with an allowlist (`name`, `value`, `path`) and no PII, then `track()` that type. Until that schema exists, do not send those metrics.

---

## 6. Queue rules

- Memory only. Do not persist the queue.
- One request carries `{ "events": [ ... ] }`. Never one HTTP call per event.
- 10 seconds or 20 events, whichever is first.
- `sendBeacon` when the document becomes hidden.
- Three retries, exponential wait, then discard.
- Throttle from the plan still applies before enqueue: `section_viewed` once per path per session per 30 seconds; `page_load_recorded` once per path per session per 60 seconds; `api_latency_recorded` only when `duration_ms` is at least 200 and at most once per method and route per 60 seconds. Do not throttle `login_failed`, `direct_stock_edit_rejected`, or `stock_threshold_triggered`.

---

## 7. Out of this phase

- No database tables and no Supabase writes for events.
- No emitters on the public site.
- No email, password, reset token, order `notes`, or staff name in `properties`.
- No second telemetry HTTP client.
- Do not rewrite root `CONTEXT.md`, the approved plan stamp files, or `memory-bank/evaluations/Results/TelemetryPlan-20260923.md`.

---

## 8. Evaluation (implementation step)

Show the scorecard in chat. Save a Results file only after a human confirms Pass.

1. `POST /telemetry/events` accepts `TelemetryEvent` batches and returns `{ "received": N }`.
2. `TelemetryEvent` has every envelope field from the plan.
3. The browser URL comes from `NEXT_PUBLIC_TELEMETRY_ENDPOINT` and is not hardcoded.
4. The API settings declare `TELEMETRY_ENDPOINT`.
5. The service queues, flushes at 10 seconds or 20 events, uses `sendBeacon` on hide, and retries three times.
6. `track()` callers do not pass envelope fields.
7. No telemetry `fetch` or `axios` outside the service.
8. Every mandatory event in §4 is instrumented.
9. Errors, performance, and navigation are instrumented, not only inventory.
10. `event_type` and property keys match the approved schema.
11. No email, name, or password in any event.
12. The browser Network tab shows a batch and a 200 response.
