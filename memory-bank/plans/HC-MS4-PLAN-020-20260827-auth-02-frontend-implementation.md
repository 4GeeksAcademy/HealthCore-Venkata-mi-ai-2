---
stamp: HC-MS4-PLAN-020
sequence: 20
milestone: MS4
date: 20260827
title: Authentication AUTH-02 Frontend Flows Implementation
status: implemented
phase: implementation
summary: Implemented backoffice login/register/profile flows with localStorage JWT lifecycle, client route protection, logout, and bearer propagation to suppliers and incidents APIs with 401 session reset handling.
related_paths:
  - uis/backoffice/app/layout.tsx
  - uis/backoffice/app/login/page.tsx
  - uis/backoffice/app/register/page.tsx
  - uis/backoffice/app/account/profile/page.tsx
  - uis/backoffice/components/auth/AuthGuard.tsx
  - uis/backoffice/components/auth/SessionActions.tsx
  - uis/backoffice/lib/auth-storage.ts
  - uis/backoffice/lib/auth-api.ts
  - uis/backoffice/lib/authed-fetch.ts
  - uis/backoffice/lib/suppliers-api.ts
  - uis/backoffice/components/incidents/IncidentAnalyzerPanel.tsx
  - uis/backoffice/app/globals.css
  - memory-bank/plans/INDEX.md
  - memory-bank/progress.md
do_not_repeat:
  - Add auth guard logic to uis/healthcore
  - Replace localStorage token flow with cookie/session middleware flow
  - Re-open supplier or incident routes without bearer token
  - Skip 401 clear-and-redirect handling on protected API calls
---

# HC-MS4-PLAN-020 - Authentication AUTH-02 Frontend Flows Implementation

## Decisions locked

- Backoffice routes are protected with a client-side auth guard and public allowlist.
- Login and register store access tokens in localStorage and redirect to protected workspace.
- Logout clears localStorage token and redirects to login.
- Protected API calls for suppliers and incidents now include bearer token and clear session on 401.
- Public website remains untouched and unauthenticated.

## Verification performed

- Added login, register, and account profile pages and linked them to backend endpoints.
- Added guarded fetch abstraction for bearer headers and centralized 401 handling.
- Updated supplier and incident API clients to require authenticated calls.
- Backoffice lint and typecheck both pass after integration.

## Agent instructions

1. Keep AUTH-02 guarded routes in backoffice only; do not copy auth logic into uis/healthcore.
2. Preserve localStorage bearer workflow for current assignment requirements.
3. Continue AUTH-03 with TinyDB reset token invalidation and user-facing forgot/reset/change-password flows.
4. Append next stamp for AUTH-03 completion and sync progress/index.
