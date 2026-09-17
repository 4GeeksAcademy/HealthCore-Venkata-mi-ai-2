# HealthCore Frontend — Performance Audit

**Date:** 2026-09-16  
**Frontends:** `uis/healthcore` (http://localhost:3000) and `uis/backoffice` (http://localhost:3001)  
**Tool:** Chrome Lighthouse Performance, **desktop** preset, Lighthouse CLI 12.8.2  
**Runtime:** `next dev` in Docker Compose (lab scores stay lower than a production `next start` build)  
**Screenshots:** [`docs/lighthouse/`](./lighthouse/)  
**Skills used:** `core-web-vitals`, `performance` (MEASUREMENT.md CLI fallback), `web-perf`, `healthcore-web-performance`

Chrome DevTools MCP was not available in this session. Measurement followed the performance skill fallback: Lighthouse CLI against runnable localhost URLs. No CrUX field data exists for localhost.

## Before

| Frontend | URL | Performance | Notes |
|----------|-----|-------------|--------|
| Public site | http://localhost:3000/ | **99** (CLI, this session) | LCP 0.9s, CLS 0. Screenshot: `lighthouse/healthcore-home-before.png` |
| Backoffice login | http://localhost:3001/login | **~75** (Chrome Lighthouse, earlier this session) | LCP was **Loading session**; Geist webfonts; client heading |
| Backoffice home | http://localhost:3001/ | **~78** | Full Operations panel JS on first paint |
| Backoffice Operations | http://localhost:3001/ops | **~89** | Client `BackofficeShell`; expanded lists |

**Root causes (not just Lighthouse flags)**

- **Backoffice LCP:** `AuthGuard` replaced the page with **Loading session** until `/auth/me` finished, so the largest paint was a client loading string instead of the login/welcome heading.
- **Backoffice fonts / CLS risk:** `next/font` Geist (and Geist Mono) downloaded on every route.
- **Backoffice JS:** Home statically imported the full Operations panel; nav prefetched other modules; `/ops` wrapped chrome in a client shell.
- **Backoffice hydration:** `SessionActions` read `localStorage` during render, so SSR HTML said Login while the client said Profile.
- **Public site LCP:** `Source_Sans_3` Google font on the root layout competed with first paint. The hero `h1` was already in HTML; the logo already had width/height/`priority`. Below-fold `PatientSignupForm` still sat on the home JS path.

## After

| Frontend | URL | Performance | Notes |
|----------|-----|-------------|--------|
| Public site | http://localhost:3000/ | **99** | LCP **0.8s** (was 0.9s), CLS 0. Screenshot: `lighthouse/healthcore-home-after.png` |
| Backoffice login | http://localhost:3001/login | **100** | LCP 0.3s, CLS 0. Screenshot: `lighthouse/backoffice-login-after.png` |

Public Performance was already 99; the measurable lab gain there is **LCP 0.9s → 0.8s** after removing the webfont and splitting the signup form. Backoffice login **~75 → 100**.
