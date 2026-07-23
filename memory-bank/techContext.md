# HealthCore — Technical Context

## Stack

| Layer | Technology |
|-------|------------|
| Language | TypeScript (strict typing required for clinical/ops entities) |
| Public UI | Next.js (App Router) + React + Tailwind — `uis/healthcore` |
| Internal UI | Next.js (App Router) + React + Tailwind — `uis/backoffice` |
| Ops logic | Pure TypeScript utilities under `src/utils/` |
| Tooling | ESLint, `tsc --noEmit`, `tsx` for tests/smoke |

Target UI package versions align with the HealthCore Digital monorepo practice: **Next.js 16**, **React 19**, **TypeScript 5**, **Tailwind 4**.

## Architecture decisions

1. **Two UI apps, zero shared layout** — `uis/healthcore` (public medical/corporate site) and `uis/backoffice` (internal Digital tools) must not share layout components or marketing chrome.
2. **Hiring tracker lives in backoffice** — The former `uis/talent-pipeline-tracker` app is migrated into `uis/backoffice` as an internal module (e.g. `/hiring`). It must never be exposed as part of the public site.
3. **Ops logic stays in `src/utils/`** — Collection, search, denial rate, no-show cost, CME compliance, and validations power Monday-morning reports for Tom, Marcus, and Diane.
4. **Stamped plans are source of truth for “already done”** — Agents read `memory-bank/plans/INDEX.md` and the latest `HC-PLAN-*` stamp before scaffolding or migrating again.

## Domain types (canonical)

Interfaces and unions for `Claim`, `Appointment`, `Clinician`, `Location`, denial reasons, service types, CME status, etc. are defined in project context (`CONTEXT.md`) and shared packages. Sample IDs such as `HC-*`, `CLM-*`, `APT-*`, `CLN-*` are **synthetic**.

## Security & privacy constraints

- Treat all patient-adjacent fields as sensitive even when synthetic in samples.
- Do **not** log free-text clinical notes, full patient names from real systems, or insurance member IDs from production.
- Do **not** commit `.env*` secrets, credentials, or production connection strings.
- Prefer HIPAA / UK GDPR–safe language in UI copy and agent notes (no inventing real patient stories).
- Public forms (e.g. patient sign-up) are client-side typed UX only unless a backend is explicitly requested; never persist PHI to public repos.

## Verification commands (reference)

```bash
# Root ops utilities
npm run typecheck
npm run test:src

# Per UI package (from package directory)
npm run lint
npx tsc --noEmit
```

## Visual identity notes

- **Public site**: medical/corporate blue + teal (`brandblue` / `brandgreen`), trustworthy spacing, HealthCore logo under `uis/image/healthcore-logo.svg`.
- **Backoffice**: distinct internal shell; must not reuse public marketing header/footer.
