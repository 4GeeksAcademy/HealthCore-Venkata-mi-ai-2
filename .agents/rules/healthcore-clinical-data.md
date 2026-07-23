# HealthCore clinical & operational data rule

**Scope:** always active for this repository.

## Enforce

1. Use strict TypeScript for HealthCore clinical/ops entities (`Claim`, `Appointment`, `Clinician`, `Location`, and related unions).
2. Never invent or commit real patient data. Sample IDs (`HC-*`, `CLM-*`, `APT-*`, `CLN-*`) are synthetic only.
3. Do not log free-text clinical notes, real phone/email from production, or insurance member identifiers.
4. Keep `uis/healthcore` (public) and `uis/backoffice` (internal) layouts completely isolated — no shared marketing chrome.
5. Prefer HIPAA / UK GDPR–safe copy in UI and agent notes.
6. When touching billing denial, no-show, or CME logic, preserve Monday-morning reliability for Tom Callahan, Marcus Reid, and Diane Foster.
