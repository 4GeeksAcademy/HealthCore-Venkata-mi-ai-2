# HealthCore Frontend — Performance Corrections Report

**Date:** 2026-09-16  
**Related audit:** [docs/audit.md](./audit.md)  
**Screenshots / scores:** [docs/lighthouse/](./lighthouse/)  
**Skills applied in this correction pass:** [`healthcore-web-performance`](../.cursor/skills/healthcore-web-performance/SKILL.md), [`core-web-vitals`](../.cursor/skills/core-web-vitals/SKILL.md) (LCP webfont + hydration), [`performance`](../.cursor/skills/performance/SKILL.md) (measure before/after; system fonts; code splitting), [`web-perf`](../.cursor/skills/web-perf/SKILL.md) (CLI lab audit when DevTools MCP is absent)

Auth was not removed. Protected backoffice routes still require a JWT and `fetchAuthMe`. Public and backoffice layouts stay isolated.

## Measurable Lighthouse results

Desktop Lighthouse CLI 12.8.2 against `next dev` in Docker.

| Frontend | Metric | Before | After |
|----------|--------|--------|--------|
| Backoffice (`/login`) | Performance score | ~75 | **100** |
| Public site (`/`) | Performance score | 99 | 99 |
| Public site (`/`) | LCP | 0.9s | **0.8s** |

At least one Lighthouse score improved on each frontend: backoffice Performance **~75 → 100**; public LCP **0.9s → 0.8s**.

---

## 1. Backoffice login / home / Operations (earlier this session)

| Problem | Correction | Skill |
|---------|------------|--------|
| First paint was **Loading session** | Public routes render immediately; session check stays on protected routes | core-web-vitals LCP (client-rendered delay) |
| Login heading lived in a client form | Server `h1` **Backoffice login** | core-web-vitals LCP in initial HTML |
| Geist webfonts | System fonts (`Segoe UI`, `system-ui`) | performance / font-display |
| Home shipped full Operations panel JS | Server `HomeOpsSummary`; full panel on `/ops` only | performance code splitting |
| Client `BackofficeShell` | `(auth)` / `(internal)` server layouts | core-web-vitals LCP |
| Expanded denial / no-show / CME lists | Headline numbers visible; details in `<details>` | performance `content-visibility` |
| `SessionActions` hydration mismatch (Login vs Profile) | Custom hook `useAuthToken` reads `localStorage` only after mount; reserved space until ready | core-web-vitals hydration / CLS |

**Files:** `AuthGuard.tsx`, `public-routes.ts`, `app/(auth)/`, `app/(internal)/`, `HomeOpsSummary.tsx`, `Milestone2OpsPanel.tsx`, `hooks/useAuthToken.ts`, `SessionActions.tsx`, `globals.css`, `next.config.ts`

---

## 2. Public site `uis/healthcore` (skill-guided pass after measurement)

Measured **before** changing public code (Performance 99, LCP 0.9s), then applied:

| Problem | Correction | Skill |
|---------|------------|--------|
| `Source_Sans_3` Google font on every page | Removed `next/font`; system stack | core-web-vitals fonts must not block text |
| Logo LCP/CLS | Already `next/image` with `width`/`height`/`priority` — left in place | core-web-vitals image dimensions |
| Below-fold signup on the home JS path | `next/dynamic` for `PatientSignupForm` | performance code splitting |
| Default Next headers | `poweredByHeader: false`, `compress: true` | performance delivery |

**Files:** `uis/healthcore/app/layout.tsx`, `uis/healthcore/app/globals.css`, `uis/healthcore/app/page.tsx`, `uis/healthcore/next.config.ts`

---

## 3. What was not changed

- JWT in `localStorage` and `/auth/me` on internal routes.
- Operations numbers still come from `src/utils`.
- Compose still runs `next dev` (hot reload), not `next start`.
- Public vs backoffice layouts are not shared.
