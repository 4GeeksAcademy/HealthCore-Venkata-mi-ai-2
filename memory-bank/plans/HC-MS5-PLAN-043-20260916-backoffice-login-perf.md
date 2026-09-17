---
stamp: HC-MS5-PLAN-043
sequence: 43
milestone: MS5
date: 20260916
title: Backoffice Login Lighthouse Performance
status: implemented
phase: implementation
summary: Improved backoffice login LCP by rendering public auth routes immediately (no Loading session gate), omitting chrome on public pages, serving the login heading from a server component, and dropping unused Geist Mono. Protected routes still wait on JWT + /auth/me.
related_paths:
  - uis/backoffice/app/layout.tsx
  - uis/backoffice/app/login/page.tsx
  - uis/backoffice/app/globals.css
  - uis/backoffice/next.config.ts
  - uis/backoffice/components/auth/AuthGuard.tsx
  - uis/backoffice/components/auth/BackofficeShell.tsx
  - uis/backoffice/components/auth/LoginForm.tsx
  - uis/backoffice/lib/public-routes.ts
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Block public /login HTML behind AuthGuard checkedPath / Loading session
  - Load Geist_Mono on every backoffice page
  - Remove the root layout Suspense around AuthGuard
  - Set turbopack.root to uis/backoffice
  - Skip fetchAuthMe on protected routes
---

# HC-MS5-PLAN-043 — Backoffice Login Lighthouse Performance

## Decisions locked

- Public routes (`/login`, `/register`, `/forgot-password`, `/reset-password`) render children immediately so Lighthouse LCP is the login heading, not “Loading session”.
- Top nav / SessionActions stay off public auth pages (`BackofficeShell`).
- Login `h1` is a server component; the form stays a client component with existing try/catch + support copy.
- Protected pages still require a token and `fetchAuthMe`.
- One sans font with `display: "swap"`.

## Agent instructions

1. Do not restore the AuthGuard loading gate on public auth routes.
2. Keep JWT + `/auth/me` checks on protected routes.
3. Keep root Suspense around AuthGuard (PLAN-038).
4. Re-run Lighthouse on `/login` after Next is Ready; scores in `next dev` stay lower than a production `next start`.
5. Append a new stamp for later work; do not rewrite this file.
