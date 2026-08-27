---
stamp: HC-MS4-PLAN-022
sequence: 22
milestone: MS4
date: 20260827
title: Authentication Demo Mode Without Realtime Email
status: implemented
phase: implementation
summary: Switched password reset to demo-safe mode with no outbound provider communication; reset links are logged locally and provider env keys were removed from the sample env template.
related_paths:
  - services/api/app/routers/auth.py
  - services/api/.env.example
  - services/api/README.md
  - memory-bank/plans/INDEX.md
  - memory-bank/progress.md
do_not_repeat:
  - Re-enable real-time outbound email providers for demo runs
  - Add provider API keys to .env.example or repository files
  - Return non-generic forgot-password response bodies
---

# HC-MS4-PLAN-022 - Authentication Demo Mode Without Realtime Email

## Decisions locked

- Forgot-password no longer performs outbound provider API calls during demo runs.
- Reset links are emitted in local API logs for functional testing.
- API response behavior remains unchanged: forgot-password always returns 200 with generic confirmation.
- Demo env template excludes provider-specific keys to avoid implied real-time communication dependencies.

## Verification performed

- Confirmed auth router compiles after removing provider network call logic.
- Confirmed documentation reflects demo-mode reset behavior.

## Agent instructions

1. Keep forgot-password in demo-safe mode unless explicitly asked to restore real providers.
2. Do not add live provider API keys to tracked files.
3. Preserve generic anti-enumeration responses for forgot-password.
