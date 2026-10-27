# `data/raw` folder

This folder is intended for **raw data** related to the company: dumps, exports, sample files, event samples, or untransformed datasets.

- **Main purpose**: serve as a landing zone or reference for original data before pipelines process it.
- **Recommendation**: document each dataset’s origin, format, expected size, privacy/PII considerations, and how it is versioned (ideally avoiding sensitive data in the repository).

> _Spanish version: [README.es.md](./README.es.md)._

## Consolidated monthly revenue (`healthcore_sales.csv`)

Official HealthCore series for the sales-forecast ticket: one `consolidated` row per month from 2016-01 through 2025-12. Columns are `month`, `revenue_usd`, `visits_count`, `avg_revenue_per_visit_usd`, `region`. Aggregated dollars and visit counts only — no patient identifiers. Do not regenerate or edit the values; the flu-season and summer pattern is already in the file. Briefing: [`docs/Project_Contexts/healthcore-sales-BRIEFING.en.md`](../../docs/Project_Contexts/healthcore-sales-BRIEFING.en.md).

## Nightly telemetry CSV backups

`scripts/nightly_export.py` writes `telemetry_YYYY-MM-DD.csv` here as an audit/recovery snapshot of `telemetry_events` for that UTC day. The monthly clinic supply pipeline reads from the database, **not** these files.
