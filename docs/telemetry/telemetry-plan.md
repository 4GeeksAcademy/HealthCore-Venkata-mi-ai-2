# HealthCore telemetry plan

Design only. Do not add emitters, collectors, or dashboards from this file until a later implementation task. The API behavior this plan instruments is already in `services/api`.

Company: HealthCore Digital. Staff tools live in `uis/backoffice`. The API lives in `services/api`. Do not instrument `uis/healthcore`.

Schemas: [event-schemas.json](./event-schemas.json) (JSON Schema draft-07). `schemaVersion` is `1.0.0`.

---

## Envelope

Every event is one JSON object. No extra top-level keys.

| Field | Rule |
|-------|------|
| `eventId` | UUID. New for every emit. |
| `timestamp` | ISO 8601 UTC, for example `2026-09-23T18:04:00+00:00`. Time the fact occurred, not the time a batch job loaded it. |
| `sessionId` | Browser session id sent as `X-Session-Id`. If the API has no session header, use the string `server`. |
| `userId` | TinyDB user id as a string (JWT `sub`). `null` when no authenticated user is known. Never an email. |
| `event_type` | `entity_action`. Verbs in this plan are closed. |
| `schemaVersion` | `1.0.0` |
| `requestId` | Correlation id. Client sends `X-Request-Id`. The API creates one when the header is missing and returns it on the response. Browser events that never hit the API mint their own id and reuse it if a request follows. |
| `properties` | Allowlisted keys only. Anything else is a bug. |

`created_by` on order JSON stays on the HTTP response for the history page. It is not an event field.

### Persistence mapping (`telemetry_events.tags`)

When the storage sink writes a row, `tags` (JSONB) is:

| Key in `tags` | Source |
|---------------|--------|
| Allowlisted property keys | `event.properties` (same allowlists as below — no extra keys) |
| `eventId` | envelope `eventId` |
| `sessionId` | envelope `sessionId` |
| `userId` | envelope `userId` (`null` when anonymous) |
| `schemaVersion` | envelope `schemaVersion` |
| `requestId` | envelope `requestId` |

Fixed columns: `timestamp`, `service` (`backoffice`), `event_type`, `level` (`info` / `warn` / `error` from event type), optional `value` from `properties.value` / `duration_ms` / `latency_ms`, optional `message`.

---

## Catalogue

**Mandatory** events are the operations floor. **Identified** events are additional opportunities. Each sentence is the reason the event exists.

### Mandatory

| `event_type` | Why |
|--------------|-----|
| `inbound_order_created` | We capture `inbound_order_created` because we need to know how much stock was received, by SKU and user, which allows us to decide whether a low-stock alert was caused by missing deliveries rather than by consumption. |
| `outbound_order_created` | We capture `outbound_order_created` because we need to know how many outbound orders are registered per day, which allows us to decide clinic consumption and whether receiving is keeping up. |
| `order_validation_failed` | We capture `order_validation_failed` because we need to know which products accumulate validation and stock errors, which allows us to decide whether a SKU’s threshold, on-hand quantity, or form rules are wrong. |
| `direct_stock_edit_rejected` | We capture `direct_stock_edit_rejected` because we need to know who attempted to set stock outside an order, which allows us to decide whether staff need retraining or a client is bypassing the order rule. |
| `stock_threshold_triggered` | We capture `stock_threshold_triggered` because we need to know when on-hand stock crosses under `threshold`, which allows us to decide which clinic SKU to reorder before the next consumption. |
| `login_failed` | We capture `login_failed` because we need to know how many failed logins happen per day and why, which allows us to decide whether to investigate a credential attack or an inactive-account problem. |
| `section_viewed` | We capture `section_viewed` because we need to know which backoffice sections operators open, which allows us to decide where to spend the next usability fix. |
| `flow_abandoned` | We capture `flow_abandoned` because we need to know which multi-step flows are left unfinished, which allows us to decide whether the inbound, outbound, register, or password-reset form should be shortened or clarified. |

### Identified opportunities

| `event_type` | Category | Why |
|--------------|----------|-----|
| `product_created` | business | We capture `product_created` because we need to know when a new SKU is born already below threshold (stock starts at 0), which allows us to decide whether catalog setup should require an inbound order before the SKU is treated as stocked. |
| `login_succeeded` | authentication | We capture `login_succeeded` because we need to know the denominator next to failed logins, which allows us to decide whether a spike in failures is an attack or a widespread outage. |
| `session_expired` | authentication | We capture `session_expired` because we need to know how often a 30-minute JWT dies during work, which allows us to decide whether to lengthen the token or warn before expiry. |
| `password_reset_failed` | authentication | We capture `password_reset_failed` because we need to know how often reset tokens are invalid or expired, which allows us to decide whether the 30-minute reset window is too short or tokens are being replayed. |
| `password_change_failed` | authentication | We capture `password_change_failed` because we need to know how often a signed-in user fails the current-password check, which allows us to decide whether the change-password form needs a clearer error or a reset path. |
| `api_latency_recorded` | performance | We capture `api_latency_recorded` because we need to know which routes are slow after the timing log is gone, which allows us to decide which cached reads or queries to tune next. |
| `page_load_recorded` | performance | We capture `page_load_recorded` because we need to know which backoffice screens take too long to become usable, which allows us to decide which route to slim or lazy-load next. |
| `api_request_failed` | errors | We capture `api_request_failed` because we need to know when the API returns 500 or 503, which allows us to decide whether to stop a task and restore the service. |
| `frontend_error_captured` | errors | We capture `frontend_error_captured` because we need to know which backoffice screens throw, which allows us to decide whether to roll back a release. |
| `flow_started` | navigation | We capture `flow_started` because we need to know how many people entered a flow, which allows us to decide the abandonment rate instead of counting abandons with no baseline. |
| `incident_analysis_completed` | business | We capture `incident_analysis_completed` because we need to know how often staff run the incident CSV analyzer and how many rows fail validation, which allows us to decide whether the upload template or the clinic file is the problem. |
| `supplier_record_changed` | business | We capture `supplier_record_changed` because we need to know when the vendor directory is created, rated, deactivated, or removed, which allows us to decide whether a Monday spend figure changed because of a directory edit. |
| `web_vital_recorded` | performance | We capture `web_vital_recorded` because we need to know which backoffice routes have poor LCP, INP, or CLS, which allows us to decide which screen to fix in the next performance pass. |

---

## Where each event is emitted

Inventory flow, in order. These are the points a later change should hook. Do not add a stock-write route.

1. Staff open a backoffice path: `section_viewed`.
2. `POST /auth/login` returns 200: `login_succeeded`. Returns 401: `login_failed`.
3. `POST /inventory/products` returns 201: `product_created`. Returns 400 because the raw JSON contained `stock` or `current_stock`: `direct_stock_edit_rejected`. Returns 400 `SKU already exists.`: `order_validation_failed` with `reason` `duplicate_sku`. Returns 422: `order_validation_failed` with `reason` `validation_error`.
4. Inbound form mounts: `flow_started` with `flow` `inbound_order`. Leave without a 201: `flow_abandoned`. `POST /inventory/orders/inbound` returns 201: `inbound_order_created`. Returns 404: `order_validation_failed` with `reason` `product_not_found`. Returns 422: `validation_error`.
5. Outbound form mounts: `flow_started` with `flow` `outbound_order`. Leave without a 201: `flow_abandoned`. `POST /inventory/orders/outbound` returns 201: `outbound_order_created`. If that body has `threshold_crossed: true`, also emit `stock_threshold_triggered` from the same before/after live totals (not from `GET /inventory/products`). Returns 400 insufficient stock: `order_validation_failed` with `reason` `insufficient_stock`. Do not emit `stock_threshold_triggered` on that 400. Returns 404 or 422: the matching validation reason.

Other hooks:

- `GET /auth/me` or any JWT check returns 401 because the token is expired: `session_expired`. Invalid or missing tokens use `reason` `token_invalid` or `token_missing` and `userId` `null`. A signature-valid expired token may set `userId` from `sub`. Never store the token.
- `POST /auth/reset-password` returns 400: `password_reset_failed`. The reset form also uses `flow_started` / `flow_abandoned` with `flow` `password_reset`.
- `POST /auth/change-password` returns 400: `password_change_failed`.
- Register page: `flow_started` / `flow_abandoned` with `flow` `register`. Success is `POST /users` 201. Do not emit the email or the name.
- Existing timing middleware: `api_latency_recorded` under the throttle below. Status 500 or 503: `api_request_failed` as well.
- `POST /api/incidents/analyze` returns 200: `incident_analysis_completed`. Do not emit CSV cells.
- Supplier `POST`, `PATCH /rate`, `PATCH /status`, `DELETE`: `supplier_record_changed`.
- Backoffice error boundary: `frontend_error_captured`.
- Backoffice route becomes usable (heading painted): `page_load_recorded`. Measure in the browser. Do not send resource URLs or query strings.

`userId` is required and non-null for inventory writes, supplier changes, incident analysis, `login_succeeded`, and `password_change_failed`, because those routes already have a JWT. It is null for `login_failed` and `password_reset_failed`.

---

## Property allowlists

Sensitive data is called out on each event. Order `notes`, staff email, passwords, reset tokens, and patient fields are never properties.

### `inbound_order_created` (mandatory, business)

No sensitive fields. `userId` is the actor.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `order_id` | integer | yes | New `inbound_order.id` |
| `product_id` | integer | yes | `medical_supply.id` |
| `sku` | string | yes | SKU copied onto the order |
| `quantity` | integer | yes | Units received, greater than 0 |

### `outbound_order_created` (mandatory, business)

No sensitive fields.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `order_id` | integer | yes | New `outbound_order.id` |
| `product_id` | integer | yes | `medical_supply.id` |
| `sku` | string | yes | SKU copied onto the order |
| `quantity` | integer | yes | Units issued |
| `threshold_crossed` | boolean | yes | Same flag as the 201 body |

### `order_validation_failed` (mandatory, business)

No sensitive fields. Do not copy the HTTP `detail` sentence. Map it to `reason`. For insufficient stock, `available_stock` is the live total already returned to the client.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reason` | string enum | yes | `validation_error`, `duplicate_sku`, `product_not_found`, `insufficient_stock` |
| `status_code` | integer | yes | 400, 404, or 422 |
| `route` | string enum | yes | `POST /inventory/products`, `POST /inventory/orders/inbound`, `POST /inventory/orders/outbound` |
| `product_id` | integer | no | Present when the request included a known id |
| `sku` | string | no | Present when the request included a SKU |
| `quantity` | integer | no | Present when the request included a quantity |
| `available_stock` | integer | no | Present only for `insufficient_stock` |

### `direct_stock_edit_rejected` (mandatory, business)

No sensitive fields. Do not record the numeric stock the client sent.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `route` | string | yes | Always `POST /inventory/products` |
| `rejected_fields` | string array | yes | One or both of `stock` and `current_stock`, unique |

### `stock_threshold_triggered` (mandatory, business)

No sensitive fields. Counts are operational stock, not patient data. Source is the outbound write’s live before/after totals.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `order_id` | integer | yes | Outbound order that caused the cross |
| `product_id` | integer | yes | `medical_supply.id` |
| `sku` | string | yes | SKU |
| `threshold` | integer | yes | Restock line on the product |
| `previous_stock` | integer | yes | Live stock before this outbound |
| `current_stock` | integer | yes | Live stock after this outbound |

`threshold_crossed` is true only when `previous_stock >= threshold` and `current_stock < threshold`. A SKU that was already below the line does not emit this event. A new product at stock 0 does not emit it; use `product_created.below_threshold`.

### `product_created` (identified, business)

No sensitive fields.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `product_id` | integer | yes | New `medical_supply.id` |
| `sku` | string | yes | SKU |
| `threshold` | integer | yes | Restock line |
| `below_threshold` | boolean | yes | True when `0 < threshold` |

### `login_failed` (mandatory, authentication)

The login body contains an email and a password. Both are dropped before emit. `userId` is null even if the email matches a user, so a failed login cannot be used to confirm an account. `reason` `inactive_user` is only used after the password check has already failed closed in the same 401 path the API uses today (`Invalid credentials` vs `Inactive user`). Do not add the email to distinguish them.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reason` | string enum | yes | `invalid_credentials` or `inactive_user` |

### `login_succeeded` (identified, authentication)

`userId` is the new session’s `sub`. Role is the enum already stored on the user (`admin`, `manager`, `user`). No email.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `role` | string enum | yes | `admin`, `manager`, or `user` |

### `session_expired` (identified, authentication)

Do not log the bearer token. If `sub` cannot be read safely, `userId` is null.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reason` | string enum | yes | `token_expired`, `token_invalid`, or `token_missing` |

### `password_reset_failed` (identified, authentication)

Do not log the token or the email. `userId` is null.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reason` | string | yes | Always `invalid_or_expired_token` |

### `password_change_failed` (identified, authentication)

`userId` is the signed-in user. Do not log either password.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reason` | string | yes | Always `current_password_incorrect` |

### `section_viewed` (mandatory, navigation)

Path is a route template, not a filled URL. `/hiring/candidates/42` is recorded as `/hiring/candidates/[id]` so a workforce id is not exported. Query strings are stripped.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `path` | string enum | yes | `/`, `/ops`, `/incidents`, `/suppliers`, `/inventory`, `/inventory/inbound`, `/inventory/outbound`, `/inventory/orders`, `/hiring`, `/hiring/candidates/[id]`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/account/profile`, `/account/change-password` |

### `flow_started` and `flow_abandoned` (navigation)

`flow_abandoned` is mandatory. `flow_started` is identified. No form field values.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `flow` | string enum | yes | `inbound_order`, `outbound_order`, `register`, `password_reset` |

Abandon means the page for that flow was left, or the component unmounted, without the success response (inbound/outbound 201, `POST /users` 201, reset-password 200). A validation error is not an abandon; the user is still in the flow. Emit `order_validation_failed` for that error and keep the flow open.

### `api_latency_recorded` (identified, performance)

No bodies, query strings, or tokens. `route_template` uses FastAPI path templates (`/inventory/products/{product_id}`), not raw ids, except that numeric ids in the path are already outside the template. `cache_status` is the existing `X-Cache` value when the route sets it, otherwise `NONE`.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `method` | string | yes | HTTP method |
| `route_template` | string | yes | Route template |
| `status_code` | integer | yes | Response status |
| `duration_ms` | number | yes | Handler time in milliseconds |
| `cache_status` | string enum | yes | `HIT`, `MISS`, or `NONE` |

### `page_load_recorded` (identified, performance)

No sensitive fields. `path` uses the `section_viewed` allowlist. `duration_ms` is time from navigation start until the route’s main heading is visible. Drop resource URLs.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `path` | string enum | yes | Same allowlist as `section_viewed` |
| `duration_ms` | number | yes | Time until the main heading is visible |
| `load_kind` | string enum | yes | `navigate` or `reload` |

### `api_request_failed` (identified, errors)

Same shape as latency, without cache and without the `detail` string (a database error detail must not leak). Status is only 500 or 503.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `method` | string | yes | HTTP method |
| `route_template` | string | yes | Route template |
| `status_code` | integer | yes | 500 or 503 |

### `frontend_error_captured` (identified, errors)

`error_name` is the error constructor name (`TypeError`, `Error`). Drop the message and the stack. They can contain anything the user typed. `path` uses the same allowlist as `section_viewed`.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `error_name` | string | yes | Constructor name, max 64 characters |
| `path` | string enum | yes | Same allowlist as `section_viewed` |

### `incident_analysis_completed` (identified, business)

Counts only. Do not emit categories, file names, or CSV cells. Incident files can describe clinic operations in free text.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `total_processed` | integer | yes | Rows the analyzer saw |
| `total_valid` | integer | yes | Rows accepted |
| `total_invalid` | integer | yes | Rows rejected |
| `duration_ms` | number | yes | Handler time |

### `supplier_record_changed` (identified, business)

`supplier_id` is the directory id. Do not emit vendor name, contact, rate amount, or notes.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `supplier_id` | integer | yes | Supplier id |
| `action` | string enum | yes | `created`, `rate_updated`, `status_updated`, `deleted` |

### `web_vital_recorded` (identified, performance)

No sensitive fields. `path` uses the `section_viewed` allowlist. `value` is the metric as reported by the browser (milliseconds for LCP, INP, FCP, and TTFB; a unitless score for CLS).

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string enum | yes | `LCP`, `INP`, `CLS`, `FCP`, or `TTFB` |
| `value` | number | yes | Browser-reported metric value |
| `path` | string enum | yes | Same allowlist as `section_viewed` |

---

## Delivery

Stream means the event should be visible within seconds, because the decision cannot wait for a nightly job. Batch means a periodic rollup is enough.

| `event_type` | Mode | Why this urgency |
|--------------|------|------------------|
| `stock_threshold_triggered` | stream | A clinic can consume the remaining units on the same shift. Reorder cannot wait until the next morning. |
| `direct_stock_edit_rejected` | stream | Repeated attempts to bypass the order rule should be visible while the session is still active. |
| `login_failed` | stream | A burst of 401s is a credential incident. A daily count is too late to block it. |
| `password_reset_failed` | stream | Replayed or guessed reset tokens are a live abuse signal. |
| `api_request_failed` | stream | 500 and 503 mean staff cannot finish the task in front of them. |
| `frontend_error_captured` | stream | A bad release should be reversible the same hour. |
| `outbound_order_created` | batch | The question is orders per day, not orders per second. |
| `inbound_order_created` | batch | Receiving volume is reviewed with the daily outbound count. |
| `order_validation_failed` | batch | “Which SKUs fail most” is a catalog decision, and the user already sees the 400 or 422. |
| `product_created` | batch | Catalog setup is reviewed with purchasing, not paged. |
| `login_succeeded` | batch | It exists to divide into the daily failure count. |
| `session_expired` | batch | Changing the 30-minute lifetime is a weekly product decision. |
| `password_change_failed` | batch | A wrong current password is a form problem, reviewed with other auth friction. |
| `section_viewed` | batch | Section popularity is a planning input, not an interrupt. |
| `flow_started` | batch | The rate is computed with abandons on a schedule. |
| `flow_abandoned` | batch | Form redesign is not a same-minute action. |
| `api_latency_recorded` | batch | Slow-route ranking feeds the next performance pass. The process log still has every request locally. |
| `page_load_recorded` | batch | A slow screen is a release-planning input. Staff already see the delay; paging on it does not restock a clinic. |
| `web_vital_recorded` | batch | Core Web Vitals guide the next performance pass. They do not page the clinic on the same shift. |
| `incident_analysis_completed` | batch | Upload quality is reviewed with operations, not paged. |
| `supplier_record_changed` | batch | Directory edits explain a later spend figure. They do not page anyone. |

### Throttle

Security and stock-alert events are not throttled: `login_failed`, `password_reset_failed`, `direct_stock_edit_rejected`, `stock_threshold_triggered`, `api_request_failed`, `frontend_error_captured`.

| Event | Rule |
|-------|------|
| `section_viewed` | At most one event per `path` per `sessionId` per 30 seconds. Rapid clicks on the same nav item are one visit. |
| `api_latency_recorded` | Emit only when `duration_ms` is at least 200, and at most one event per `method` + `route_template` per 60 seconds per process. Keep the max `duration_ms` in that window. Faster calls stay in the process log only. |
| `page_load_recorded` | At most one event per `path` per `sessionId` per 60 seconds. Keep the max `duration_ms` in that window. |
| `web_vital_recorded` | At most one event per metric `name` and `path` per `sessionId` per 60 seconds. |
| `flow_started` | At most one per `flow` per `sessionId` until that flow succeeds or is abandoned. Remounting the same form is not a new start. |

No other event is high-frequency enough to debounce. One outbound order is one business fact.

---

## Risks and exclusions

Discarded on purpose:

- **Public site (`uis/healthcore`).** Patient-facing. A page view or form error there can carry patient-adjacent data. This plan is for staff operations.
- **Order `notes`.** Free text. A delivery note can name a person or a clinic story. The order id, SKU, and quantity answer the stock questions without it.
- **Email, password, reset token, and `created_by`.** Login failures must not confirm that an email exists. `userId` is the staff key when a session exists.
- **The numeric stock a client tried to write.** The rejection only needs the field names. The value is not a fact the system accepted.
- **Stock-page color as an alert.** `stock < threshold` on `/inventory` is a display of current state, and the product list can be 30 seconds stale. The alert is only the downward cross on a successful outbound.
- **Hiring candidate fields and incident CSV contents.** Names, CV links, and incident text are out. Section visits and analysis counts stay.
- **Supplier name, rate, and contact.** The directory change is enough to explain that a spend input moved.
- **Frontend error message and stack.** They can echo typed input.
- **Keystroke, mouse, and full URL query telemetry.** High volume, and query strings can carry tokens (`/reset-password?token=`).
- **A new route that writes `current_stock`.** Stock still changes only through orders. Gap A rejects `stock` and `current_stock` on product create. It does not add an editor.
- **Paths that are not in this API.** Do not emit `/auth/password-reset` or `/api/suppliers`. Live auth paths are `/auth/login`, `/auth/me`, `/auth/forgot-password`, `/auth/reset-password`, and `/auth/change-password`. Suppliers are `/suppliers`.

Cost: `section_viewed` and `api_latency_recorded` are the noisy pair. The throttle above is the control. Do not sample `stock_threshold_triggered` or `login_failed` to save volume.

---

## Implementation notes for the next change

- Validate every emit against [event-schemas.json](./event-schemas.json) before it leaves the process. Drop the event and log a local schema-failure counter if it does not validate. Do not log the rejected payload.
- One `requestId` ties the browser event, the API event, and the existing timing log line.
- `outbound_order_created` and `stock_threshold_triggered` share `order_id` when both fire.
- Do not put these events in the product-list cache or in `created_by`.
