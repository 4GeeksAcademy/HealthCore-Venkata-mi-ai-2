# Telemetry Plan Assignment Evaluation

**Date:** 2026-09-23  
**Rubric:** “What to Evaluate” (ten telemetry-plan checks)  
**Design as of:** [HC-MS5-PLAN-061](../../plans/HC-MS5-PLAN-061-20260923-page-load-telemetry.md)  
**Saved after:** [HC-MS5-PLAN-062](../../plans/HC-MS5-PLAN-062-20260923-telemetry-plan-eval.md)  
**Overall: PASS (10/10)**

| Doc | Path |
|-----|------|
| CONTEXT | [`docs/Project_Contexts/CONTEXT-telemetry-plan.md`](../../../docs/Project_Contexts/CONTEXT-telemetry-plan.md) |
| Plan | [`docs/telemetry/telemetry-plan.md`](../../../docs/telemetry/telemetry-plan.md) |
| Schemas | [`docs/telemetry/event-schemas.json`](../../../docs/telemetry/event-schemas.json) |

Saved after human confirmation of the chat scorecard. This evaluation does not close or reopen MS5. No telemetry emitters were part of this score.

## Method

- Compared the plan’s mandatory events with CONTEXT §6 (names, labels, and when each fires).
- Counted hypothesis sentences, categories, and stream/batch rows against the 20-event catalogue.
- Draft-07 schema check (`Draft7Validator.check_schema`) plus a property-name compare of every allowlist to the markdown tables.
- Sample events validated: `outbound_order_created`, `login_failed`, `direct_stock_edit_rejected`, `stock_threshold_triggered`, `section_viewed`, `flow_abandoned`, `page_load_recorded`. Events that added `email` or `notes` were rejected.
- Gap behavior that the plan instruments was already covered by `python -m pytest` in `services/api`: **57 passed** (PLAN-059).

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Every mandatory metric from the company context is present and correctly identified | **Pass** | All eight CONTEXT floor events are labelled mandatory: `outbound_order_created`, `order_validation_failed`, `direct_stock_edit_rejected`, `stock_threshold_triggered`, `login_failed`, `section_viewed`, `flow_abandoned`, and companion `inbound_order_created`. |
| 2 | Technical and business opportunities, broadly, not only the mandatory floor | **Pass** | 12 identified events across authentication, performance, errors, navigation, and business (catalog, incidents, suppliers). |
| 3 | Every event has a hypothesis and a decision | **Pass** | 20 “We capture … because … which allows us to decide …” sentences, one per event. |
| 4 | Envelope is consistent and includes the eight required fields | **Pass** | Schema `required` is `eventId`, `timestamp` (ISO 8601), `sessionId`, `userId`, `event_type` (`entity_action`), `schemaVersion` `1.0.0`, `requestId`, `properties`. |
| 5 | Every event has a documented property allowlist | **Pass** | Markdown tables plus `additionalProperties: false` on the envelope and on every event definition. |
| 6 | `event-schemas.json` is valid and matches the plan | **Pass** | Draft-07 schema checks. Property names match. Extra `email` and `notes` keys fail validation. |
| 7 | Stream vs batch is justified by urgency | **Pass** | Each of the 20 events has an operational reason (reorder the same shift, credential burst, daily order count, weekly form review). |
| 8 | Sensitive data or PII is identified, with sanitisation | **Pass** | Email, password, reset token, order `notes`, error message/stack, incident CSV cells, and hiring ids are named and dropped. `userId` is the TinyDB id or null. |
| 9 | Risks and exclusions discard events for a reason | **Pass** | Public site, stock-page color as an alert, keystroke/query telemetry, and a stock-write API are excluded with privacy, staleness, or cost reasons. |
| 10 | Another developer can instrument without clarification | **Pass** | Hooks name the route, status, and reason code (`POST /inventory/orders/outbound` 201, Gap A 400 detail, `threshold_crossed`, login 401 reasons). |

## Residuals (do not fail the rubric)

- No emitters, collectors, or dashboards. This score is the design only.
- `page_load_recorded` measures time until the route’s main heading is visible. The implementer still chooses the heading element on each page.

## Verdict

The HealthCore telemetry plan matches the context floor, covers staff backoffice opportunities beyond that floor, and the JSON schema enforces the allowlists. **PASS (10/10).**
