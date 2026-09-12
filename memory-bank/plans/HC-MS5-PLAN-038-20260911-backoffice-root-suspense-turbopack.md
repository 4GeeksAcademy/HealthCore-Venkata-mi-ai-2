---
stamp: HC-MS5-PLAN-038
sequence: 38
milestone: MS5
date: 20260911
title: Backoffice Root Suspense and Turbopack Root
status: implemented
phase: implementation
summary: Wrapped AuthGuard/usePathname in a root Suspense boundary so Next.js 16 does not show the Issue overlay, and pinned turbopack.root to the monorepo so @hc ops imports resolve.
related_paths:
  - uis/backoffice/app/layout.tsx
  - uis/backoffice/next.config.ts
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Remove the root layout Suspense around AuthGuard
  - Set turbopack.root to uis/backoffice (breaks @hc/utils imports)
  - Restore TinyDB inventory or a writable stock column
  - Commit .env or DATABASE_URL passwords
  - Rewrite PLAN-037 or MS5_Project_Eval.md
---

# HC-MS5-PLAN-038 — Backoffice Root Suspense and Turbopack Root

## Decisions locked

- Root layout wraps `AuthGuard` (uses `usePathname`) in `Suspense`.
- `turbopack.root` is the monorepo root so Milestone 2 `@hc` aliases work.

## Agent instructions

1. Keep the root Suspense boundary around AuthGuard.
2. Keep turbopack.root at the repo root, not `uis/backoffice`.
3. Append a new stamp for later work; do not rewrite this file.
