---
stamp: HC-MS5-PLAN-053
sequence: 53
milestone: MS5
date: 20260918
title: Backend Serialization Audit Context And Response Models
status: implemented
phase: implementation
summary: Saved serialization CONTEXT, closed health/analyze/delete-user/register-email gaps, documented CSV export exception, updated pytest for register without email.
related_paths:
  - docs/Project_Contexts/CONTEXT-backend-serialization-audit.md
  - docs/serialization-audit.md
  - docs/README.md
  - services/api/app/models/health.py
  - services/api/app/models/incidents.py
  - services/api/app/models/users.py
  - services/api/app/main.py
  - services/api/app/routers/users.py
  - services/api/app/routers/incidents.py
  - services/api/tests/test_register.py
  - services/api/tests/test_token.py
  - services/api/tests/test_inventory.py
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Put email back on POST /users or GET /users JSON
  - Drop inventory created_by email
  - Add a JSON response_model on CSV export
  - Save a serialization evaluation file until a human confirms Pass
---

# HC-MS5-PLAN-053 — Backend Serialization Audit Context And Response Models

## Decisions locked

- Register is `POST /users`. Nested `user` has no email.
- `GET /auth/me` may return email. User list/get/put do not.
- Inventory `created_by` stays staff email for backoffice history.
- `GET /api/incidents/results/export` is a CSV `Response`, not JSON.

## Agent instructions

1. Do not rewrite this stamp or the CONTEXT after a human confirm.
2. Show serialization rubric results in chat; save an eval file only after the user confirms Pass.
3. Keep TinyDB auth vs SQLModel inventory split; do not return raw store rows as HTTP JSON.
