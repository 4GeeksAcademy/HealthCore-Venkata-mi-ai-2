# CONTEXT: HealthCore Telemetry Plan

**Audience:** AI coding agents working in the HealthCore Digital monorepo.  
**Parent:** [CONTEXT.md](../../CONTEXT.md) (canonical product).  
**Related:** [CONTEXT-inventory-orm-dual-database.md](./CONTEXT-inventory-orm-dual-database.md), [CONTEXT-MS5-inventory-backoffice.md](./CONTEXT-MS5-inventory-backoffice.md), [auth_master_framework_Context.md](./auth_master_framework_Context.md).  
**Last updated:** 2026-09-23

This file is the company brief for the telemetry assignment. It is not the telemetry plan.

**Status (2026-09-23):** Gap A and Gap B are implemented in `services/api`. The design is [`docs/telemetry/telemetry-plan.md`](../telemetry/telemetry-plan.md) and [`docs/telemetry/event-schemas.json`](../telemetry/event-schemas.json). Do not instrument application code from this CONTEXT alone; follow the telemetry plan.

---

## 1. Work order

Both steps below are done. Do not redo them. The next task, if asked, is instrumentation that follows the telemetry plan.

1. **Gaps (done).** [§4](#4-gaps-to-close-before-the-telemetry-plan) is implemented in `services/api`.
2. **Telemetry plan (done).** [`docs/telemetry/telemetry-plan.md`](../telemetry/telemetry-plan.md) and [`docs/telemetry/event-schemas.json`](../telemetry/event-schemas.json). No emitters were added.

---

## 2. Why this exists at HealthCore

HealthCore Digital runs the staff backoffice (`uis/backoffice`) and the FastAPI API (`services/api`) for clinic operations: medical-supply inventory, auth, suppliers, incidents, hiring, and Monday ops (denial rate, no-show cost, CME). Operations can ask questions the running system does not answer: how many outbound orders are registered per day, which products collect the most validation errors, whether anyone tries to set stock directly, when minimum-stock alerts fire, how many logins fail, which sections staff open, and which flows they abandon.

The public site `uis/healthcore` is out of this assignment. It is patient-facing. Do not instrument it and do not share layouts with the backoffice.

Root `CONTEXT.md` has no telemetry metric table. The mandatory floor is the operations questions above, named with the entities in this repo.

---

## 3. What the API does today

Inventory tables (SQLModel): `medical_supply`, `inbound_order`, `outbound_order`. Auth, users, profiles, and suppliers stay in TinyDB.

`MedicalSupply` columns are `id`, `name`, `sku`, `threshold`. `current_stock` is not stored. It is inbound quantity minus outbound quantity (`current_stock_for` in `services/api/app/inventory/service.py`).

| Method | Path | What it does |
|--------|------|----------------|
| GET | `/inventory/products` | JWT. Cached 30s (`X-Cache`). A list read can be up to 30s stale. |
| POST | `/inventory/products` | Body `name`, `sku`, `threshold` (`threshold >= 0`). New row `current_stock` is 0. Duplicate SKU is **400** `SKU already exists.` |
| GET | `/inventory/products/{product_id}` | **404** `Product not found.` |
| POST | `/inventory/orders/inbound` | Body `product_id`, `quantity` (`> 0`), `notes`. Stores `user_uuid`. |
| POST | `/inventory/orders/outbound` | Same body. Live SQL stock check, never the product cache. **400** `Insufficient stock. Available: {n}. Requested: {n}.` |
| GET | `/inventory/orders` | Inbound and outbound history. `created_by` is staff email resolved at read time. |

There is no `PUT`, `PATCH`, or `DELETE` on products or orders. `POST /inventory/products` does not accept stock. Extra JSON keys are ignored, so a body that includes `stock` or `current_stock` still creates the product and leaves stock at 0.

Low stock on the stock page is a browser comparison: `stock < threshold` (`uis/backoffice/types/inventory.ts`, `ProductStockPanel`). The API does not record a crossing.

Auth (TinyDB, JWT lifetime 30 minutes):

| Method | Path | Failure the plan must be able to count |
|--------|------|----------------------------------------|
| POST | `/auth/login` | **401** `Invalid credentials` or `Inactive user` |
| GET | `/auth/me` | Missing or expired JWT |
| POST | `/auth/forgot-password` | Always the same public message. Do not log whether the email exists. |
| POST | `/auth/reset-password` | **400** `Invalid or expired token` |
| POST | `/auth/change-password` | **400** `Current password is incorrect` |

Register is `POST /users`, not `/auth/register`. There is no `/auth/password-reset`. Suppliers are `/suppliers`, not `/api/suppliers`. Incidents are `POST /api/incidents/analyze` and `GET /api/incidents/results/export` (CSV). Liveness is `GET /health`. The browser calls the API through the backoffice `/hc-api` rewrite.

Other validation already returned by the API (not gaps): `quantity <= 0` or `threshold < 0` is **422**; unknown `product_id` on an order is **404**; database failure on an order write is **503**.

Backoffice paths: `/`, `/ops`, `/incidents`, `/suppliers`, `/inventory`, `/inventory/inbound`, `/inventory/outbound`, `/inventory/orders`, `/hiring`, `/hiring/candidates/[id]`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/account/profile`, `/account/change-password`.

---

## 4. Gaps to close before the telemetry plan

Implement these in `services/api` before writing `docs/telemetry/`. Add or extend pytest coverage. Do not add a route that writes `current_stock`. Do not emit telemetry events in the gap change.

### Gap A — Reject a direct stock edit

**Today:** `POST /inventory/products` parses `MedicalSupplyCreate` and drops unknown keys. Sending `stock` or `current_stock` succeeds and does not change stock. The operations question “are users trying to modify stock directly and getting rejected?” has no rejection to count.

**Required behavior:** If the JSON object for `POST /inventory/products` contains `stock` or `current_stock`, do not insert a row. Respond **400** with this exact detail:

`Stock cannot be modified directly. Register an inbound or outbound order.`

Apply the check to the raw object, before the ignored-extra behavior can drop those keys. A body with only `name`, `sku`, and `threshold` stays **201**. Duplicate SKU stays **400** `SKU already exists.` `PUT` and `PATCH` on products stay absent (method not allowed). Do not add them.

Inbound and outbound bodies are the legal stock change. Do not reject `quantity` on those routes. Do not treat `notes` as a stock edit.

### Gap B — Record the moment stock crosses under the threshold

**Today:** After a successful outbound, stock can move from at-or-above `threshold` to below it, and nothing on the response says so. The stock page only paints rows that are already low. That cannot answer “when do the minimum stock threshold alerts fire?”

**Required behavior:** On **201** from `POST /inventory/orders/outbound`, include `threshold_crossed` (boolean) on `OutboundOrderResponse`.

- Compare live stock for that `product_id` before the new outbound row is counted with stock after it is committed.
- `threshold_crossed` is **true** only when previous stock was `>= threshold` and new stock is `< threshold`.
- It is **false** when stock was already below threshold, or when it stays at or above threshold.
- Use the same live totals as the insufficient-stock check, not `GET /inventory/products` cache.
- A **400** insufficient-stock response does not include the flag and does not change stock.
- Inbound increases stock, so it does not fire this alert. Do not add `threshold_crossed` to inbound.
- A new product starts at stock 0. If `threshold > 0` it is born low. That is not an alert fire. The telemetry plan will treat it as product creation with `below_threshold`, not as `stock_threshold_triggered`.

Existing order fields stay: `id`, `product_id`, `product_name`, `quantity`, `notes`, `created_at`, `user_uuid`, `created_by`.

### Out of the gap change

- No `docs/telemetry/` files.
- No changes to `uis/healthcore`.
- No new stock column and no product update route.
- No change to the 30s product-list TTL. The crossing flag is on the outbound write, which already uses live SQL.
- Do not rewrite root `CONTEXT.md` or prior plan stamps.

---

## 5. Telemetry plan design task

After Gaps A and B are in the API, write the design. Another developer must be able to instrument it without asking what an event means. Still do not ship instrumentation in that step.

Deliverables, both under `docs/telemetry/`:

- `telemetry-plan.md`
- `event-schemas.json` (JSON Schema draft-07, consistent with the markdown)

**Golden rule.** Every event must complete: we capture `[event_type]` because we need to know `[hypothesis]`, which allows us to make the decision `[concrete decision]`. If that sentence cannot be completed, the event does not exist.

**Catalogue.** Mandatory metrics are a floor. Also catalogue technical and business opportunities across the backoffice: authentication, performance, uncaught frontend errors, and navigation (sections visited, flows abandoned). Classify each event **mandatory** (from the floor in §6) or **identified opportunity**.

**Envelope.** Every event includes `eventId`, `timestamp` (ISO 8601), `sessionId`, `userId`, `event_type` (`entity_action`, consistent verbs), `schemaVersion`, `requestId` (joins browser, API, and logs), and `properties`.

**Schemas.** Full schemas for every mandatory metric, plus at least eight additional events from at least three categories (business/inventory, authentication, performance, errors, navigation). For each event: `event_type`, description, property allowlist (name, type, required or optional, description), and whether it contains sensitive data or PII and how that is removed before emit. Keys outside the allowlist are forbidden.

**Delivery.** For each designed event, stream or batch, justified by how fast the decision is needed. Document throttle or debounce for high-frequency events. Include risks and exclusions: events considered and discarded, and data not captured for privacy or cost.

---

## 6. HealthCore binding for the plan

Use these names. Do not invent a generic warehouse, a stock column, or an alert service that the gap work does not add.

**Mandatory floor** (label them mandatory):

| Operations question | `event_type` to use | Fires when |
|---------------------|---------------------|------------|
| Outbound orders per day | `outbound_order_created` | `POST /inventory/orders/outbound` returns 201 |
| Validation errors by product | `order_validation_failed` | 422, 400 duplicate SKU, 404 unknown product, or 400 insufficient stock. Properties include `product_id` and `sku` when known, `status_code`, and a stable `reason` code. Never `notes`. |
| Direct stock edit rejected | `direct_stock_edit_rejected` | Gap A returned 400. Properties: `route`, `rejected_fields` (`stock` and/or `current_stock`). No stock value. |
| Minimum-stock alert | `stock_threshold_triggered` | Gap B set `threshold_crossed` true. Properties: `product_id`, `sku`, `threshold`, `previous_stock`, `current_stock`. |
| Failed logins per day | `login_failed` | `POST /auth/login` returns 401. Properties: `reason` (`invalid_credentials` or `inactive_user`). No email and no password. |
| Sections staff open | `section_viewed` | Backoffice navigations listed in §3. Property: `path` from that allowlist. |
| Flows abandoned | `flow_abandoned` | Inbound, outbound, register, or password reset started and left without the success response. Property: `flow` from an allowlist. |

Also design `inbound_order_created` as a mandatory companion so outbound counts are not the only stock movement.

**Identity.** `userId` is `user_uuid` (TinyDB user id as a string, JWT `sub`). `created_by` email stays on the HTTP order payload for the history page and stays out of events. Unauthenticated events (failed login, public auth pages) may omit `userId`; do not substitute an email.

**Privacy.** No patient names, member IDs, or clinical free text. No staff email, password, reset token, or order `notes` in `properties`. Inventory has no PHI. Do not add any.

**Stock source.** `stock_threshold_triggered` uses the outbound write’s live before/after totals. Do not define that event off the cached `GET /inventory/products` body.

**Exclusions the plan must keep:** `uis/healthcore`; raw `notes`; email on login failure; a stock-mutation API; calling the stock-page color chip an alert fire; documenting `/auth/password-reset` or `/api/suppliers` as live paths.

**Examples that already fit the taxonomy** (use these verbs; extend the catalogue past this list): `inbound_order_created`, `outbound_order_created`, `stock_threshold_triggered`, `direct_stock_edit_rejected`, `order_validation_failed`, `login_failed`, `session_expired`, `api_latency_recorded`, `section_viewed`, `flow_abandoned`.

---

## 7. Evaluation (design step)

Score the telemetry plan only after Gaps A and B are done. Pass only if every item passes.

1. Every mandatory metric in §6 is present and labelled mandatory.
2. The catalogue covers technical opportunities (errors, performance, authentication, navigation) and business opportunities, beyond the mandatory floor.
3. Every event has a hypothesis and a decision.
4. The envelope is the same on every event and includes the eight fields in §5.
5. Every event has a property allowlist.
6. `event-schemas.json` validates and matches the markdown.
7. Stream vs batch is justified by decision urgency.
8. Sensitive fields are named, with the sanitisation in §6.
9. Risks and exclusions include the discarded cases in §6.
10. A developer can instrument from the plan without inventing routes, status codes, or field names.
