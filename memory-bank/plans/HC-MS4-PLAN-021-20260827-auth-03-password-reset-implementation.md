---
stamp: HC-MS4-PLAN-021
sequence: 21
milestone: MS4
date: 20260827
title: Authentication AUTH-03 Password Recovery and Change Implementation
status: implemented
phase: implementation
summary: Implemented forgot-password, reset-password, and change-password API plus backoffice forgot/reset/change-password pages using TinyDB reset token hashing, expiry, single-use invalidation, and provider-based email dispatch hooks.
related_paths:
  - services/api/app/models/users.py
  - services/api/app/stores/auth_store.py
  - services/api/app/routers/auth.py
  - services/api/requirements.txt
  - services/api/.env.example
  - services/api/README.md
  - uis/backoffice/app/login/page.tsx
  - uis/backoffice/app/forgot-password/page.tsx
  - uis/backoffice/app/reset-password/page.tsx
  - uis/backoffice/app/account/change-password/page.tsx
  - uis/backoffice/lib/auth-api.ts
  - memory-bank/plans/INDEX.md
  - memory-bank/progress.md
do_not_repeat:
  - Persist plaintext reset tokens in TinyDB
  - Accept reset token reuse after success
  - Return different forgot-password response for unknown email
  - Commit real provider keys or .env files
---

# HC-MS4-PLAN-021 - Authentication AUTH-03 Password Recovery and Change Implementation

## Decisions locked

- Reset tokens are random URL-safe strings hashed with SHA-256 before TinyDB storage.
- Token rows include expires_at and used_at; used/expired/missing tokens return 400.
- Forgot-password endpoint always returns the same success message to prevent email enumeration.
- Change-password requires valid JWT and rejects wrong current password with 400.
- Backoffice includes forgot, reset, and authenticated change-password flows with user feedback.

## Verification performed

- Added API endpoints: /auth/forgot-password, /auth/reset-password, /auth/change-password.
- Added reset token persistence and consume logic with one-time use invalidation.
- Added backoffice pages and login linking for password recovery journey.
- Backoffice lint and typecheck pass with new auth UI paths.
- API module compile pass succeeds with new AUTH-03 backend logic.

## Agent instructions

1. Keep reset token behavior one-time and expiry-enforced in TinyDB.
2. Keep forgot-password response generic for both known and unknown addresses.
3. Configure either Resend or SendGrid through env vars only; do not hardcode provider keys.
4. If extending auth further, append new plan stamps without rewriting prior history.
