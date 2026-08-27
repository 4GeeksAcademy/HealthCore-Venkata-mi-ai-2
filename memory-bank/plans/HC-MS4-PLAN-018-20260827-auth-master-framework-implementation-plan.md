---
stamp: HC-MS4-PLAN-018
sequence: 18
milestone: MS4
date: 20260827
title: Authentication Master Framework Implementation Task Board
status: planned
phase: planning
summary: Task-board execution plan for AUTH-01, AUTH-02, and AUTH-03 from the locked context, preserving JWT bearer, TinyDB auth storage, backoffice-only auth UI, and public-site isolation.
related_paths:
  - docs/Project_Contexts/auth_master_framework_Context.md
  - services/api/app/main.py
  - services/api/app/routers/suppliers.py
  - services/api/app/routers/incidents.py
  - services/api/requirements.txt
  - uis/backoffice/app/layout.tsx
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Implement AUTH-02 before AUTH-01 is demonstrable in API docs
  - Implement AUTH-03 before login/register/profile/logout/401 redirect are working end-to-end
  - Add authentication to uis/healthcore
  - Use cookie or session authentication instead of JWT bearer
  - Store User or Profile auth records in suppliers TinyDB
  - Change locked route prefixes /auth, /users, /profiles
---

# HC-MS4-PLAN-018 - Authentication Master Framework Implementation Task Board

## Decisions locked

- Execution is split into three graded tasks: AUTH-01, AUTH-02, AUTH-03.
- API auth contract is stateless JWT bearer with sub and exp claims.
- User, Profile, and reset token records are TinyDB-only in `services/api/data/auth.json`.
- Authentication UI and client guard exist only in backoffice surfaces.
- Public website remains unauthenticated and unchanged.
- Existing supplier and incident domain behavior must remain intact while securing access.

## Task board

### AUTH-01 (feature/auth-api)

- [ ] Add auth dependencies and env documentation.
- [ ] Implement auth core modules, models, stores, and routers.
- [ ] Implement register, login, me, users, and profiles endpoints.
- [ ] Enforce ownership and admin checks for protected user mutations.
- [ ] Protect all six supplier routes and both incident routes.
- [ ] Keep `GET /health` public.
- [ ] Verify `401` on missing/invalid/expired token and `403` on forbidden cross-user access.

### AUTH-02 (feature/auth-frontend)

- [ ] Add backoffice auth storage, API client helpers, and guarded fetch.
- [ ] Build login, register, and profile pages.
- [ ] Guard protected backoffice views with client-side token checks.
- [ ] Attach bearer token to all protected HealthCore API calls.
- [ ] Implement logout and global `401` handling with redirect to login.
- [ ] Confirm public site remains unaffected.

### AUTH-03 (feature/password-reset)

- [ ] Implement forgot-password with anti-enumeration response behavior.
- [ ] Implement reset-password with hashed token, expiry check, and single-use invalidation.
- [ ] Implement authenticated change-password endpoint.
- [ ] Integrate one email provider (Resend preferred) and document env vars.
- [ ] Build forgot, reset, and change-password UI flows in backoffice.
- [ ] Verify expired/reused token and wrong current password error paths.

## Agent instructions

1. Follow the locked context in `docs/Project_Contexts/auth_master_framework_Context.md` exactly for route prefixes, status codes, and storage rules.
2. Ship AUTH-01, AUTH-02, and AUTH-03 as separate branches and PRs in sequence.
3. Keep supplier and incident payload contracts unchanged while adding token protection.
4. Keep auth concerns out of `uis/healthcore`.
5. After each shipped task, append a new plan stamp and update `memory-bank/plans/INDEX.md` and `memory-bank/progress.md`.
6. Use PHI-safe commit messages and never commit secrets or `.env` files.
