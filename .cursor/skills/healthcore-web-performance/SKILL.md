---
name: healthcore-web-performance
description: >-
  Apply HealthCore constraints while using the core-web-vitals, performance,
  and web-perf skills. Use when optimizing Lighthouse scores, Core Web Vitals
  (LCP, INP, CLS), page speed, or frontend performance in uis/backoffice or
  uis/healthcore.
---

# HealthCore web performance

Read these skills first, then apply the HealthCore constraints below:

1. [core-web-vitals](../core-web-vitals/SKILL.md)
2. [performance](../performance/SKILL.md)
3. [web-perf](../web-perf/SKILL.md)

Upstream sources:

- https://www.skills.sh/addyosmani/web-quality-skills/core-web-vitals
- https://www.skills.sh/addyosmani/web-quality-skills/performance
- https://www.skills.sh/cloudflare/skills/web-perf

## HealthCore constraints

- Public app is `uis/healthcore`. Internal app is `uis/backoffice`. Do not share layouts or marketing chrome.
- Do not invent Lighthouse or Core Web Vitals scores. Record lab conditions (`next dev` vs `next start`).
- `next dev` (including Docker Compose) scores are lower than a production `next start` build.
- Keep JWT + `/auth/me` on protected backoffice routes. Do not restore a full-page **Loading session** gate on public `/login`.
- Operations metrics stay on `/ops` from `src/utils`. User-facing label is **Operations**; do not rename the `/ops` URL.
- Before/after notes: [`docs/audit.md`](../../../docs/audit.md). Code corrections: [`docs/report.md`](../../../docs/report.md).
- Do not commit `.env` files or secrets. Sample IDs (`HC-*`, `CLM-*`) are synthetic.
