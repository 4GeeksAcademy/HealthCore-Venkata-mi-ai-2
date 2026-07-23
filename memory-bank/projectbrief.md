# HealthCore — Project Brief

## Company

HealthCore is an outpatient healthcare services company operating **12 clinics** across the United States (Texas, Florida, Georgia) and the United Kingdom (London, Manchester). The network processes roughly **600 patient visits per week**, manages insurance billing across US and UK payer systems, and employs **200+ clinical and administrative staff**.

**HealthCore Digital** is the internal technology unit that modernises clinical and operational workflows. Project owner: **James Osei, CTO**.

## Mission

Deliver reliable, typed software that improves outpatient operations without compromising patient privacy (HIPAA / UK GDPR). Numbers that reach Tom Callahan (billing), Marcus Reid (clinical operations), and Diane Foster (people / workforce) every Monday morning must be trustworthy.

## Core problems HealthCore solves with this codebase

1. **Billing denial tracking (Tom Callahan)** — Denial rates are still calculated manually from CSV exports. HealthCore needs consistent denial-rate logic by payer and location, plus flagging of payers above the 5–8% industry benchmark (default alert threshold: **8%**).
2. **No-show cost estimation (Marcus Reid)** — Clinics lack a weekly estimate of revenue lost to no-shows. HealthCore needs per-location no-show cost and rate calculations using clinic average consultation fees (default high no-show alert: **20%**).
3. **CME compliance monitoring (Diane Foster)** — Continuing medical education hours live in spreadsheets with no risk alerts. HealthCore needs CME status (`on_track` | `at_risk` | `overdue` | `complete`) and licence-expiry alerts (recommended: **90** / **30** day thresholds).
4. **Workforce hiring visibility (Diane Foster)** — Internal backoffice must host the People & Workforce Hiring Tracker so clinic staffing pipelines stay visible to HealthCore Digital staff (not on the public website).

## Service lines (public + clinical context)

Primary care, chronic disease, preventive, specialist, women’s health, paediatric, and mental health — delivered as outpatient care across US and UK sites.

## Product surfaces (planned workspace)

| Surface | Path | Audience |
|---------|------|----------|
| Public website | `uis/healthcore` | Patients, referring physicians, public |
| Static entry (rewritten pointer) | `uis/index.html` | Thin entry to the public Next app |
| Internal backoffice | `uis/backoffice` | HealthCore Digital / ops / people team |
| Ops TypeScript utilities | `src/utils/` | Denial, no-show, CME, validation logic |

## Success criteria

- Strict TypeScript models for claims, appointments, clinicians, and locations.
- No real PHI in logs, commits, or sample data narratives.
- Public and backoffice UIs remain layout-isolated.
- Agent sessions always load this brief, tech context, progress, and the latest stamped plan under `memory-bank/plans/` before changing HealthCore code.
