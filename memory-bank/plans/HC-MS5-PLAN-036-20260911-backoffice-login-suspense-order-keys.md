---
stamp: HC-MS5-PLAN-036
sequence: 36
milestone: MS5
date: 20260911
title: Backoffice Login Suspense and Order History Keys
status: implemented
phase: implementation
summary: Wrapped login and reset-password useSearchParams in Suspense so Next.js no longer shows the Issue overlay, and keyed order-history rows by type plus id so inbound and outbound ids do not collide.
related_paths:
  - uis/backoffice/app/login/layout.tsx
  - uis/backoffice/app/reset-password/layout.tsx
  - uis/backoffice/components/inventory/OrderHistoryPanel.tsx
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Remove the login/reset-password Suspense layouts
  - Key merged inbound/outbound rows by numeric id alone
  - Restore mashed inventory table names or a writable stock column
  - Commit .env or DATABASE_URL passwords
  - Rewrite PLAN-034, PLAN-035, or MS5_Project_Eval.md
---

# HC-MS5-PLAN-036 — Backoffice Login Suspense and Order History Keys

## Decisions locked

- `/login` and `/reset-password` keep `useSearchParams` but sit under a parent `Suspense` boundary (Next.js App Router requirement).
- Order history React keys are `${type}-${id}` because inbound and outbound tables have separate id sequences.
- Dual-store inventory contract from PLAN-034/035 is unchanged.

## Agent instructions

1. Keep the login and reset-password Suspense layouts.
2. Keep composite keys on merged order-history rows.
3. Do not restore TinyDB inventory or mashed SQLModel table names.
4. Append a new stamp for later work; do not rewrite this file.
