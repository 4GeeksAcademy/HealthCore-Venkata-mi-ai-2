# `docs` folder

This folder holds **cross-cutting documentation** for the monorepo: architecture guides, technical decisions, conventions, processes, and any material shared across applications, pipelines, agents, and workflows.

- **Main purpose**: provide a single place for “global” project documentation (not tied to one app or agent only).
- **Recommendation**: organize docs by topic (architecture, deployment, data, security, observability, etc.) and keep links from each component’s README to these guides.

> _Spanish version: [README.es.md](./README.es.md)._

## Project CONTEXTs

Assignment CONTEXTs for implementing agents live in [`Project_Contexts/`](./Project_Contexts/):

- [IncidentFileAnalyzer.md](./Project_Contexts/IncidentFileAnalyzer.md)
- [SupplierDirectory_TinyDb_API.md](./Project_Contexts/SupplierDirectory_TinyDb_API.md)
- [auth_master_framework_Context.md](./Project_Contexts/auth_master_framework_Context.md) — AUTH-01 / AUTH-02 / AUTH-03
- [CONTEXT-inventory-orm-dual-database.md](./Project_Contexts/CONTEXT-inventory-orm-dual-database.md) — **first:** inventory ORM + TinyDB/Supabase dual database
- [CONTEXT-MS5-inventory-backoffice.md](./Project_Contexts/CONTEXT-MS5-inventory-backoffice.md) — **next:** MS5 inventory backoffice UI on that API
- [CONTEXT-MS5-container.md](./Project_Contexts/CONTEXT-MS5-container.md) — MS5 / ticket `#infra-40` development Docker Compose

