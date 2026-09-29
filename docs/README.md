# `docs` folder

This folder holds **cross-cutting documentation** for the monorepo: architecture guides, technical decisions, conventions, processes, and any material shared across applications, pipelines, agents, and workflows.

- **Main purpose**: provide a single place for “global” project documentation (not tied to one app or agent only).
- **Recommendation**: organize docs by topic (architecture, deployment, data, security, observability, etc.) and keep links from each component’s README to these guides.

> _Spanish version: [README.es.md](./README.es.md)._

## Project CONTEXTs

Assignment CONTEXTs for implementing agents live in [`Project_Contexts/`](./Project_Contexts/):

- [IncidentFileAnalyzer.md](./Project_Contexts/IncidentFileAnalyzer.md)
- [SupplierDirectory_TinyDb_API.md](./Project_Contexts/SupplierDirectory_TinyDb_API.md)
- [auth_master_framework_Context.md](./Project_Contexts/auth_master_framework_Context.md) — AUTH-01 / AUTH-02 / AUTH-03
- [CONTEXT-inventory-orm-dual-database.md](./Project_Contexts/CONTEXT-inventory-orm-dual-database.md) — **first:** inventory ORM + TinyDB/Supabase dual database
- [CONTEXT-MS5-inventory-backoffice.md](./Project_Contexts/CONTEXT-MS5-inventory-backoffice.md) — **next:** MS5 inventory backoffice UI on that API
- [CONTEXT-MS5-container.md](./Project_Contexts/CONTEXT-MS5-container.md) — MS5 / ticket `#infra-40` development Docker Compose
- [CONTEXT-backend-serialization-audit.md](./Project_Contexts/CONTEXT-backend-serialization-audit.md) — FastAPI `response_model` / auth email policy
- [Performance_Optimisation_Caching.md](./Project_Contexts/Performance_Optimisation_Caching.md) — lazy load, `useMemo`, FastAPI TTL cache
- [CONTEXT-telemetry-plan.md](./Project_Contexts/CONTEXT-telemetry-plan.md) — telemetry brief; gaps closed; design in `docs/telemetry/`
- [CONTEXT-telemetry-frontend-capture.md](./Project_Contexts/CONTEXT-telemetry-frontend-capture.md) — backoffice `track()` capture; stub `POST /telemetry/events` is implemented (PLAN-064)
- [CONTEXT-telemetry-storage.md](./Project_Contexts/CONTEXT-telemetry-storage.md) — replace stub with Supabase `telemetry_events` bulk persist (per-event validate)

## Telemetry

- [telemetry-plan.md](./telemetry/telemetry-plan.md) — event catalogue, envelope, stream vs batch, exclusions
- [event-schemas.json](./telemetry/event-schemas.json) — JSON Schema draft-07 for the envelope and property allowlists
- Telemetry plan eval (2026-09-23, **10/10 Pass**) — [Results/TelemetryPlan-20260923.md](../memory-bank/evaluations/Results/TelemetryPlan-20260923.md)
- Telemetry capture eval (2026-09-25, **12/12 Pass**) — [Results/TelemetryCapture-20260925.md](../memory-bank/evaluations/Results/TelemetryCapture-20260925.md)
- Telemetry storage eval (2026-09-28, **8/8 Pass**) — [Results/TelemetryStorage-20260928.md](../memory-bank/evaluations/Results/TelemetryStorage-20260928.md)

## Audits

- [CACHING_REPORT.md](./CACHING_REPORT.md) — caching decisions, TTLs, invalidation, what was not cached
- Caching eval (2026-09-21, **8/8 Pass**, re-run) — [Results/Caching-20260921.md](../memory-bank/evaluations/Results/Caching-20260921.md)

- [serialization-audit.md](./serialization-audit.md) — API route → Pydantic schema map (CSV export excepted)
- Serialization eval (2026-09-18, **6/6 Pass**) — [Results/BackendSerialization-20260918.md](../memory-bank/evaluations/Results/BackendSerialization-20260918.md)
- [audit.md](./audit.md) — Lighthouse before/after for public site and backoffice, with root causes
- [report.md](./report.md) — Corrections plus measurable scores
- [lighthouse/](./lighthouse/) — Committed Lighthouse screenshots
- [EVALUATION.md](./EVALUATION.md) — Latest 2026-09-16 session rubric score (overwrite on re-eval the same day)

