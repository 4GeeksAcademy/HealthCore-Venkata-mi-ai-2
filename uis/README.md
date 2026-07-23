# `uis` folder

This folder contains **all HealthCore user interfaces** for the cross-functional AI Engineering project.

| App / entry | Path | Audience | Run |
|-------------|------|----------|-----|
| Public website | [`healthcore/`](./healthcore/) | Patients & public | `cd uis/healthcore && npm run dev` → port **3000** |
| Internal backoffice | [`backoffice/`](./backoffice/) | HealthCore Digital staff | `cd uis/backoffice && npm run dev` → port **3001** |
| Thin static entry | [`index.html`](./index.html) | Developers / agents | Points to the apps above (not a full marketing site) |

## Notes

- Public and backoffice layouts are **isolated** — do not share marketing chrome.
- The People & Workforce Hiring Tracker (Diane Foster) lives at **`/hiring`** inside backoffice.
- The former standalone `talent-pipeline-tracker` app was migrated into backoffice and retired.
- Shared assets: [`image/healthcore-logo.svg`](./image/healthcore-logo.svg).

> _Spanish version: [README.es.md](./README.es.md)._
