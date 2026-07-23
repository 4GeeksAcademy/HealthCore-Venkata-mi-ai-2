# HealthCore Backoffice

Internal Next.js + TypeScript workspace for HealthCore Digital staff. Layout is fully independent of `uis/healthcore`.

## Run

```bash
cd uis/backoffice
npm install
npm run dev
```

Open [http://localhost:3001](http://localhost:3001).

## Routes

- `/` — Welcome screen + **Milestone 2 ops metrics panel** (from `src/utils`)
- `/ops` — Full Milestone 2 ops dashboard (denials, no-shows, CME)
- `/hiring` — People & Workforce Hiring Tracker (Diane Foster)
- `/hiring/candidates/[id]` — Candidate detail
- `/api/records...` — Hiring tracker API routes
