# HealthCore — FastAPI Architecture Proposal

## Purpose

This document proposes a FastAPI backend architecture for **HealthCore Digital**, the internal technology unit of HealthCore (CTO: James Osei). It is a future-state, HIPAA- and UK GDPR–aware API design for HealthCore’s monorepo:

- Public medical/corporate site — `uis/healthcore` (local `:3000`)
- Internal Digital backoffice — `uis/backoffice` (local `:3001`; `/ops` and `/hiring`)
- Existing ops logic — `src/utils` (denial rate, no-show cost, CME compliance; currently TypeScript)

The workspace today is TypeScript and Next.js. This proposal describes how a FastAPI service under `backend/` should be structured when HealthCore introduces a Python API layer for the same four ops domains and hiring workflows—without scaffolding that backend in this document.

---

## 1. Company and System Context

| Field | Detail |
|-------|--------|
| **Company** | HealthCore — outpatient healthcare services network |
| **Technology unit** | HealthCore Digital (CTO: James Osei) |
| **Footprint** | 12 clinics across the United States (Texas, Florida, Georgia) and the United Kingdom (London, Manchester) |
| **Operational scale** | Roughly 600 patient visits per week; insurance billing across US and UK payer systems |
| **Workforce** | 200+ clinical and administrative staff |
| **Service lines** | Primary care, chronic disease, preventive, specialist, women’s health, paediatric, and mental health |
| **Compliance posture** | HIPAA (US) and UK GDPR; no real PHI in logs, commits, or sample narratives |
| **Primary stakeholders** | Tom Callahan (billing), Marcus Reid (clinical operations), Diane Foster (people / workforce) |

### Primary domains

1. **Billing denial tracking** — Denial-rate logic by payer and location; flag payers above the industry benchmark (default alert: **8%**).
2. **No-show cost estimation** — Per-location no-show cost and rate using clinic average consultation fees (default high no-show alert: **20%**).
3. **CME compliance monitoring** — CME status (`on_track` | `at_risk` | `overdue` | `complete`) and licence-expiry alerts (**90** / **30** day thresholds).
4. **Workforce hiring visibility** — People & Workforce Hiring Tracker for HealthCore Digital staff only (never on the public website).

---

## 2. Architectural Pattern

This section evaluates four backend architectures against HealthCore’s needs, then recommends one.

### 2.1 Evaluation criteria

- **Four cohesive ops domains** — billing denials, no-show cost, CME compliance, and hiring share locations, clinicians, and Monday-morning reporting.
- **Operational scale** — 12 clinics, ~600 visits/week, 200+ staff; a focused Digital unit.
- **Regulatory posture** — HIPAA / UK GDPR; PHI-adjacent data must stay out of loose layers, logs, and over-broad API responses.
- **Client model** — Decoupled Next.js apps (`uis/healthcore`, `uis/backoffice`); FastAPI primarily serves backoffice ops and hiring.
- **Metric trust** — Denial (8%), no-show (20%), and CME / licence windows (90 / 30 days) must be testable and consistent for Tom, Marcus, and Diane.

### 2.2 Candidate architectures

#### A. Layered Architecture with Clean Architecture principles

A modular monolith where dependencies point inward: HTTP adapters → application services → domain rules; infrastructure (DB, files, external systems) at the edge.

```text
API / Presentation  →  Application (Services)  →  Domain  →  Infrastructure
     (routers)              (use cases)         (rules)     (DB, files, external)
```

In FastAPI terms: thin routers + Pydantic schemas, services for use cases, domain packages for denial / CME / no-show / hiring rules, repositories for persistence.

**Pros**

- Clear separation of HTTP, business policy, and data access—maps to FastAPI routers, services, and DI via `Depends`.
- Domain rules (thresholds, CME status machine) can be unit-tested without HTTP or a database.
- PHI-safe response shaping is easier when Pydantic schemas sit above persistence models.
- Fits HealthCore Digital: one deployable API, shared types across four domains, low ops overhead.
- Compatible with later extraction of a service or scheduled job without rewriting the domain core.

**Cons**

- Requires layer discipline; fat routers or “god” services can still appear without review.
- Must be modularized by domain packages or it becomes a messy monolith.
- Weaker independent team scaling than microservices if Digital later splits into many squads.

**HealthCore fit:** Strong. Matches current scale, shared ops vocabulary (`src/utils` domains), and privacy needs.

---

#### B. MVC (Model–View–Controller)

Classic web pattern: Controllers handle requests, Models hold data/state, Views render output. In an API-only FastAPI world, “View” is JSON serialization; Controllers become route handlers; Models often blur ORM entities and business rules.

**Pros**

- Familiar to many developers; quick to scaffold.
- Low ceremony for small CRUD (e.g. simple hiring field updates).

**Cons**

- Under-specifies where HealthCore *policy* lives (denial formulas, CME status transitions)—logic accumulates in controllers or anemic models.
- FastAPI has no classic server-rendered View; forcing MVC labels onto routers/schemas/ORM creates confusion.
- Higher risk of fat controllers returning ORM rows and leaking PHI-adjacent fields.
- Harder to keep the four HealthCore domains consistent when “Model” means both persistence and business rules.

**HealthCore fit:** Weak as the primary architecture for regulated ops metrics and multi-domain policy.

---

#### C. Microservices

Independent deployable services per capability (billing, appointments, CME, hiring), each with its own data store and API, coordinated over the network.

**Pros**

- Independent deploy and scale per domain if traffic or ownership diverges sharply.
- Failure isolation (e.g. hiring outage need not take down denial reporting, if designed well).
- Clear ownership boundaries when multiple squads own different products.

**Cons**

- Distributed complexity: discovery, auth propagation, tracing, versioned contracts, eventual consistency.
- HealthCore’s domains share locations, clinicians, and reporting windows—early splits force duplication or chatty cross-service calls.
- Operational cost is high for a Digital unit serving 12 clinics; benefit is low at ~600 visits/week.
- Monday-morning aggregates that span domains become multi-service orchestration problems.

**HealthCore fit:** Not preferred as the starting shape. Revisit only if team count, traffic, or release cadence later demands independent deployables.

---

#### D. Serverless (Function-as-a-Service)

Business capabilities as discrete cloud functions triggered by HTTP, queues, or schedules, often behind a managed API gateway.

**Pros**

- Strong for scheduled HealthCore jobs (nightly CME licence alerts, batch denial imports).
- Pay-per-use and automatic scale for sparse workloads.
- Encourages small, focused units of work.

**Cons**

- Cold starts, timeouts, and local-dev friction hurt a cohesive interactive backoffice API (`/ops`, `/hiring`).
- Shared domain types across billing / appointments / CME are awkward across many functions.
- Observability and PHI-safe logging must be reinvented per function unless a heavy platform layer is added.
- CORS, auth, and OpenAPI versioning are harder to keep uniform than in one FastAPI app.

**HealthCore fit:** Situational later for jobs and alerts—not the primary architecture for the staff-facing REST API.

### 2.3 Comparative summary

| Pattern | Strength for HealthCore | Main weakness | Verdict |
|---------|-------------------------|---------------|---------|
| **Layered / Clean** | Cohesive domains, testable policy, PHI-aware boundaries, FastAPI-native | Requires layer discipline | **Recommended** |
| **MVC** | Familiar, fast CRUD | Weak policy boundaries; fat controllers; poor FastAPI “View” fit | Not preferred |
| **Microservices** | Independent deploy/scale later | Premature distributed cost for shared ops domains | Not preferred (now) |
| **Serverless** | Good for scheduled/alert jobs | Poor primary shape for cohesive backoffice API | Situational (later) |

### 2.4 Recommendation: Layered / Clean Architecture

**HealthCore Digital should adopt Layered Architecture with Clean Architecture principles as the primary pattern for its FastAPI backend.**

**Over MVC.** MVC does not give HealthCore a clear home for denial-rate policy, no-show formulas, or the CME status machine. Route handlers would absorb that logic or ORM models would double as business rules—raising PHI leakage risk and weakening Monday-morning trust. Layered/Clean keeps policy in domain/application layers and routers thin.

**Over Microservices.** Billing, appointments, CME, and hiring share clinic and clinician context. Splitting services at current scale multiplies deployment and consistency cost without improving outcomes for Tom, Marcus, or Diane. A layered modular monolith keeps one deployable API with domain packages; services can be extracted later if needed.

**Over Serverless-as-primary.** Serverless fits scheduled CME alerts or batch denial imports, but backoffice needs a stable `/api/v1` REST surface, shared schemas, CORS for the two Next.js apps, and consistent staff auth. That is one FastAPI application; functions can call the same domain layer later.

#### Decision statement

```text
API / Presentation  →  Application (Services)  →  Domain  →  Infrastructure
     (routers)              (use cases)         (rules)     (DB, files, external)
```

Dependencies point inward. HTTP adapters know about schemas and services; domain rules do not import FastAPI or ORM details. All following sections assume this architecture.

---

## 3. Backend Folder and Module Structure

### Proposed layout

```text
backend/
  app/
    main.py                 # Composition root: app factory, middleware, router mount
    api/
      router.py             # Aggregates versioned routers
      v1/
        health.py           # Liveness / readiness
        billing.py          # Denial tracking / claims summaries
        appointments.py     # No-show metrics
        clinicians.py       # CME / licence compliance
        hiring.py           # Candidate / pipeline APIs (internal)
        auth.py             # Staff auth for backoffice only
    schemas/
      billing.py
      appointments.py
      clinicians.py
      hiring.py
      common.py             # Shared pagination, error envelopes
    domain/
      billing/              # Denial rules, payer thresholds (aligns with src/utils)
      appointments/         # No-show rate / cost rules
      clinicians/           # CME status machine, licence windows
      hiring/               # Pipeline stages, candidate invariants
    services/               # Use-case orchestration per domain
    repositories/           # Persistence interfaces + implementations
    core/
      config.py             # Settings (env-backed)
      security.py
      logging.py
      cors.py
      exceptions.py
    deps/                   # FastAPI dependency providers
  tests/
    unit/
    integration/
    api/
```

### Criteria for domain and responsibility separation

- **Separation of concerns.** Routers handle HTTP only. Services orchestrate use cases. Domain modules own business rules (denial benchmarks, no-show formulas, CME status transitions). Repositories own I/O.
- **Business-capability boundaries.** Modules align with HealthCore’s four primary domains and stakeholder ownership (Tom → billing, Marcus → appointments/no-shows, Diane → CME and hiring).
- **Data vs business layers.** Repositories never encode denial or CME policy. Services never return raw ORM rows. Schemas omit PHI-adjacent fields that Monday-morning consumers do not need.
- **Public vs internal surfaces.** Hiring and full ops APIs serve `uis/backoffice` only. `uis/healthcore` stays layout-isolated and must not consume hiring or sensitive ops endpoints.

---

## 4. FastAPI Endpoints and Routers Organization

Routers are grouped by primary domain under `/api/v1`. Descriptions are **conceptual** (no implementation code).

### Router mounting

- `main` creates the FastAPI app, registers CORS and exception handlers, and includes `api/router`.
- `api/router` mounts each domain router with a clear prefix and OpenAPI tags.
- Each domain router stays thin: validate via Pydantic → call a service → return a response schema.

### Domain route map

#### Health (`/api/v1/health`)

- Liveness check for process health.
- Readiness check for critical dependencies (database connectivity).

#### Auth (`/api/v1/auth`) — backoffice staff only

- Staff sign-in / sign-out and current-user profile for authorized Digital staff.
- **Locked approach:** session/cookie auth aligned with the Next.js backoffice (`uis/backoffice`). No public patient auth API on this surface.

#### Billing / claims (`/api/v1/billing`)

- Claims summaries for denial analysis (synthetic IDs such as `CLM-*` in non-prod).
- Denial-rate aggregates by payer and by location / clinic.
- Payers (or payer–location pairs) exceeding the **8%** alert threshold.
- Detail views for Tom Callahan’s Monday-morning denial workflow.

#### Appointments / no-shows (`/api/v1/appointments`)

- No-show aggregates by location; per-location **rate** and **cost** (clinic average consultation fees).
- Locations exceeding the **20%** high no-show alert.
- Weekly summaries for Marcus Reid’s clinical operations reporting.

#### Clinicians / CME (`/api/v1/clinicians`)

- Clinician compliance summaries (synthetic IDs such as `CLN-*` in non-prod).
- CME status filtered by `on_track` | `at_risk` | `overdue` | `complete`.
- Licence-expiry alerts within **90** and **30** day windows.
- Detail endpoints for Diane Foster’s CME risk review.

#### Hiring / candidates (`/api/v1/hiring`)

- Candidate list, filters, stage transitions, and stage/notes history.
- Pipeline visibility for HealthCore Digital staff (maps to backoffice `/hiring`).

**Constraint:** Hiring routes are internal-only. They must never be part of the public patient-facing surface.

### Consumer guidance

| Consumer | Expected API use |
|----------|------------------|
| `uis/backoffice` | Primary authenticated client for billing, appointments, clinicians/CME, and hiring (`/ops`, `/hiring`) |
| `uis/healthcore` | Does **not** consume ops or hiring APIs; remains a layout-isolated public site |

---

## 5. FastAPI Industry Standards and Design Influence

Conventions below were researched from the **official FastAPI documentation** and applied to HealthCore’s proposed `backend/` layout (routers by domain, Pydantic schemas, dependency injection, CORS, and environment-based settings).

| Industry convention | How it influenced this design | Official source |
|---------------------|-------------------------------|-----------------|
| Package root under `app/` with `main` as composition root; routers in separate modules | Startup, middleware, and router wiring in one place; one router file per HealthCore domain (`billing`, `appointments`, `clinicians`, `hiring`) | [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) |
| Path operations / endpoint modules | Conceptual `/api/v1/...` route map grouped by domain, not a single routes file | [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) |
| Pydantic models for request/response schemas | Schemas separate from persistence so member IDs and clinical free text are not leaked in JSON | [Body — Multiple Parameters / Pydantic models](https://fastapi.tiangolo.com/tutorial/body/) (Pydantic integration is core FastAPI) |
| Dependency injection via `Depends` | Injects settings, DB sessions, and staff auth without global state | [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) |
| Environment-based settings (no secrets in repo) | Thresholds (8%, 20%, 90/30), CORS origins, and DB URLs come from environment—aligned with HealthCore’s `.env*` protection rule | [Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/) |
| Explicit CORS middleware with allowlisted origins | Supports `uis/healthcore` (`:3000`) and `uis/backoffice` (`:3001`) without `*` + credentials in production | [CORS (Cross-Origin Resource Sharing)](https://fastapi.tiangolo.com/tutorial/cors/) |
| Central exception handlers and structured logging | Consistent error envelopes; PHI-safe logs (no clinical notes or real member IDs) | FastAPI exception-handling patterns applied to HealthCore privacy rules |
| API versioning (`/api/v1`) | Lets ops formulas and hiring workflows evolve without breaking backoffice clients overnight | Common API practice combined with Bigger Applications router prefixes |

### Sources (explicit)

1. FastAPI — Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
2. FastAPI — First Steps: https://fastapi.tiangolo.com/tutorial/first-steps/
3. FastAPI — Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
4. FastAPI — CORS: https://fastapi.tiangolo.com/tutorial/cors/
5. FastAPI — Settings and Environment Variables: https://fastapi.tiangolo.com/advanced/settings/
6. FastAPI — Request Body / Pydantic models: https://fastapi.tiangolo.com/tutorial/body/

These sourced conventions keep a FastAPI modular monolith maintainable for HealthCore’s regulated outpatient network.

---

## 6. Frontend / Backend Separation Architecture

HealthCore already runs two Next.js apps with **zero shared layout**. A FastAPI backend reinforces that decoupling: UIs own presentation; the API owns domain contracts and persistence. Ops logic that today lives in `src/utils` and is shown on backoffice `/ops` is the reference domain vocabulary for the future API.

### Monorepo vs separate repositories

| Approach | Trade-offs for HealthCore |
|----------|---------------------------|
| **Monorepo (recommended)** | FastAPI under `backend/` beside `uis/healthcore`, `uis/backoffice`, and `src/utils`. Shared CI and domain vocabulary (`Claim`, `Appointment`, `Clinician`, `Location`). |
| **Separate repositories** | Independent release cadence, but duplicated types and more friction for a small Digital unit. |

**Recommendation:** Keep FastAPI in this monorepo as `backend/`. Extract a separate repo only when ownership or release cadence clearly diverges.

### API communication strategies

- **REST over JSON** with FastAPI’s OpenAPI schema as the contract source; version under `/api/v1`.
- Authenticate backoffice calls with **session/cookie auth** aligned with Next.js (`uis/backoffice` staff only).
- Prefer idempotent GETs for Monday-morning metric reads; use explicit write verbs for hiring mutations.
- TypeScript clients use DTOs that mirror Pydantic schemas—not database shapes.

### Managing environment variables

- **Backend:** Secrets and connection strings only in server-side env (never in the Next.js public bundle). Settings cover API keys, DB URLs, CORS origins, and alert thresholds.
- **Frontend:** Public vars only for non-secret config (e.g. `NEXT_PUBLIC_API_BASE_URL`). Auth secrets stay server-side.
- **Local ports:** `uis/healthcore` `:3000`, `uis/backoffice` `:3001`, FastAPI on its own port; staging and production each define origin allowlists and base URLs.
- **Protected practice:** Do not commit `.env*` files or production connection strings.

### Cross-Origin Resource Sharing (CORS)

- Allowlist exact origins for the public site and backoffice per environment.
- Do **not** use wildcard origins with credentials in production.
- Configure methods/headers for JSON + cookie/session auth as needed by backoffice.
- Hiring and ops APIs assume authenticated backoffice origins; public origins must not gain access by CORS misconfiguration alone (authorization remains mandatory).

```text
Browser (uis/backoffice primary; uis/healthcore not for ops/hiring)
        │  HTTPS + CORS allowlist
        ▼
   FastAPI /api/v1/...
        │
        ▼
  Services → Domain → Repositories
```

---

## 7. Risks and Points of Attention

### Risk 1: Layer leakage and PHI exposure

**Failure mode:** Denial or CME logic lives in routers, or ORM models are returned as API responses.

**Consequences:** Responses may include member IDs or clinical free text; tests entangle HTTP/DB; Monday-morning numbers for Tom and Marcus become unreliable; HIPAA / UK GDPR posture weakens.

**Mitigation:** Thin routers; persistence → domain → Pydantic response schemas; ban logging of clinical free text and real member IDs.

### Risk 2: CORS and environment misconfiguration across public vs backoffice

**Failure mode:** Allowlists omit the backoffice origin, use `*`, or share one env file between `uis/healthcore` and `uis/backoffice`.

**Consequences:** Backoffice `/ops` and `/hiring` fail with CORS errors while the API looks healthy; overly permissive origins can expose hiring APIs beyond Digital staff; HealthCore Digital wastes time distinguishing “API down” from “origin not allowlisted.”

**Mitigation:** Per-environment origin allowlists; separate public vs backoffice config; never pair wildcard CORS with credentials; verify both apps against the API in each deploy checklist.

### Risk 3: Collapsing four domains into unstructured modules

**Failure mode:** Billing, appointments, CME, and hiring share a single “utils” or “routes” dump (contrary to the domain packages above and the existing `src/utils` domain split).

**Consequences:** Merge conflicts and unclear ownership as Tom’s, Marcus’s, and Diane’s workflows evolve; accidental coupling (e.g. hiring importing claim persistence) slows Digital delivery.

**Mitigation:** One router / schema / service / domain package family per primary domain from day one.

---

## Summary

**Recommend Layered / Clean Architecture** for HealthCore’s FastAPI backend (over MVC, Microservices, and Serverless-as-primary). Organize `backend/` around billing denials, no-show estimation, CME compliance, and workforce hiring—aligned with `src/utils` and backoffice `/ops` + `/hiring`. Serve `uis/backoffice` as the authenticated API client; keep `uis/healthcore` off ops/hiring APIs. Follow FastAPI conventions (router-per-domain, Pydantic schemas, DI, env settings, explicit CORS). Deviating risks PHI leakage, broken or insecure cross-origin access, and unowned modules.
