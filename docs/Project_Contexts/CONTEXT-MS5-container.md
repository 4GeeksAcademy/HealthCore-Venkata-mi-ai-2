# HealthCore Digital — Development Containerization (MS5 / Ticket #infra-40)

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Document type:** Assignment CONTEXT (Dockerfiles, Compose, env, samples, evaluation, and post-implementation runbook)  
**Audience:** External implementing agent, then any squad member who runs Compose  
**Status:** Implemented — development Compose (`#infra-40`); not a production deploy  
**Ticket:** `#infra-40`  
**Milestone:** MS5 (containerization overlay; does **not** replace the inventory CONTEXT)

This CONTEXT is the **single source of truth** for dockerizing the HealthCore monorepo for **local development**. Company framing: [`CONTEXT-healthcore-briefing.en.md`](./CONTEXT-healthcore-briefing.en.md). Do **not** treat root `CONTEXT.md` as the Docker contract. Do **not** rewrite [`CONTEXT-MS5-inventory-backoffice.md`](./CONTEXT-MS5-inventory-backoffice.md) or [`CONTEXT-inventory-orm-dual-database.md`](./CONTEXT-inventory-orm-dual-database.md).

**After implementation:** skip to [How to run after implementation](#how-to-run-after-implementation).

---

## External agent — start here

You are building a **reproducible development environment** for HealthCore Digital. This is not a production cluster, not Kubernetes, and not a 4Geeks folder-name copy-paste.

The product already exists:

| Surface | Real path | Host port today |
|---------|-----------|-----------------|
| Public medical/corporate site | `uis/healthcore` | `3000` |
| Internal Digital backoffice | `uis/backoffice` | `3001` |
| FastAPI (auth, suppliers, incidents, inventory) | `services/api` | `8001` |

The academy brief says `/uis/website`. In **this** repository that app is **`uis/healthcore`**. There is no `uis/website` folder. Creating one is a rubric miss.

### Before any file change

1. Read [`AGENTS.md`](../../AGENTS.md).
2. Read [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md).
3. Read [`memory-bank/techContext.md`](../../memory-bank/techContext.md).
4. Read [`memory-bank/progress.md`](../../memory-bank/progress.md).
5. Read [`memory-bank/plans/INDEX.md`](../../memory-bank/plans/INDEX.md) and the latest stamp.
6. Create the **root** `.env` **before** writing `docker-compose.yml`.

### How to ship

| Step | Scope |
|------|--------|
| This file | Docker contract, samples, test cases, evaluation, runbook |
| Later implementation stamp | Dockerfiles, ignore files, `uis/start.sh`, Compose, env wiring, backoffice rewrite only |

After shipping Docker files: lint/typecheck any touched UI; append a **new** plan stamp; update `INDEX.md` and `progress.md`. Do **not** rewrite this CONTEXT except with explicit human confirmation.

---

## Business framing

**From:** James Osei, CTO  
**To:** HealthCore Digital squad  
**Ticket:** `#infra-40`

Every new clone currently turns into a dependency debugging session (Node versions, Python/uv, ports, `localhost` URLs that only work on one laptop). The squad needs `docker compose up` from the repository root to start the **full development platform**.

Project owner: **James Osei**. Compliance: Claire Whitfield (HIPAA / UK GDPR). Docker files are versioned — treat leaked secrets as compromised. Sample IDs (`HC-*`, …) stay synthetic. No PHI in logs, Compose, or Dockerfiles.

---

## In scope (ticket `#infra-40` only)

These files and behaviours are the assignment:

| Deliverable | Requirement |
|-------------|-------------|
| `uis/Dockerfile` | Official **Node Alpine**. Install deps for **both** Next apps. Default `CMD` runs `start.sh`. |
| `uis/start.sh` | Starts both Next.js **dev** servers: public app **3000**, backoffice **3001**. |
| `uis/.dockerignore` | At least `node_modules`, `.next`, `.env*`, `*.log`. |
| `services/Dockerfile` | Official **Python**. `uv pip install "-r" requirements.txt`. Uvicorn **`--reload`**. |
| `services/.dockerignore` | At least `tests`, `.env*`, `*.log`, `__pycache__` / `*.pyc`. |
| Root `docker-compose.yml` | Two services (UI + API), bind mounts, dev commands, published ports, **named** network, `env_file: .env`. |
| Root `.env` | All service env **names** here. Not hardcoded in YAML. File is gitignored. |
| Runtime | `docker compose up` from repo root starts both containers. Hot reload via bind mounts. Inter-service URLs use the **Compose service name**, not `localhost`. No secrets in Dockerfiles or Compose. |

HealthCore mapping that is **in scope** because otherwise Compose will not run this repo:

- Ticket `website` → `uis/healthcore` (do not create `uis/website`).
- FastAPI sources and `requirements.txt` live in `services/api/` while the Dockerfile stays at `services/Dockerfile`.
- API port stays **8001** (existing backoffice defaults).
- Bind-mount repo-root `src/` so backoffice `@hc` imports still resolve.
- Backoffice `/hc-api` rewrite so the **UI container** calls `http://api:8001` (service name) while Chrome on the host still uses `localhost:3001`. This is wiring, not a new product feature.

---

## Out of scope (do not do in this ticket)

- Production images, multi-stage prod builds, TLS, Kubernetes, Terraform, or files under `infra/`.
- A third Compose service (Postgres, Redis, mail, test runner).
- Auto-running `seed.py` as a required API entrypoint (optional later; not `#infra-40`).
- New UI pages, restyles, shared layouts, or public-site API calls.
- Auth, inventory, supplier, or incident **domain** changes.
- New error-handling UI, pytest/Jest suites, or CI workflows for Compose.
- Changing CORS to Docker hostnames.
- Committing `.env` / `.env.example`, or putting secrets in YAML.
- Rewriting root `CONTEXT.md` or the inventory/auth CONTEXTs.

---

## Rubric mapping (authoritative — do not reinterpret)

| Ticket wording | HealthCore meaning | Do **not** do |
|----------------|--------------------|---------------|
| `/uis/website` | `uis/healthcore` | Create `uis/website` |
| `/uis/backoffice` | `uis/backoffice` | Share layouts with the public site |
| `/services` FastAPI | Build from `services/`; app is `services/api` (`app.main:app`) | A second API |
| UI ports 3000 and 3001 | healthcore `:3000`, backoffice `:3001` | Two UI containers, or both apps on 3000 |
| Inter-service host | Compose DNS name `api` | `localhost` / `127.0.0.1` / raw IP **between containers** |
| Secrets | Root `.env` (gitignored) | Passwords/keys in YAML or Dockerfiles |
| Hot reload | Bind mounts + `next dev` + `uvicorn --reload` | Production `next start` as the Compose command |

---

## Locked contracts (do not invent)

### Compose topology

| Compose service | Build context | Role |
|-----------------|---------------|------|
| `ui` | `./uis` (`dockerfile: Dockerfile`) | Both Next.js apps, **one** container |
| `api` | `./services` (`dockerfile: Dockerfile`) | FastAPI + Uvicorn `--reload` |

Named network (required): **`healthcore`**.

Published ports (host → container):

| Host | Container | Process |
|------|-----------|---------|
| `3000` | `3000` | `uis/healthcore` `next dev` |
| `3001` | `3001` | `uis/backoffice` `next dev` |
| `8001` | `8001` | `uvicorn app.main:app` |

Do not silently switch the API to `8000`.

Both processes must bind **`0.0.0.0`**, or the host browser cannot reach them.

### Inter-service vs host browser

| Caller | Allowed host | Example |
|--------|----------------|---------|
| `ui` container → `api` container | Docker service name | `http://api:8001` |
| Developer browser on the laptop | `localhost` + published ports | `http://localhost:3001` |
| Password-reset **link** a human clicks | Host origin | `BACKOFFICE_PUBLIC_URL=http://localhost:3001` |

`NEXT_PUBLIC_*` is inlined for the **browser**. `NEXT_PUBLIC_AUTH_API_URL=http://api:8001` **breaks** login because Chrome cannot resolve `api`.

**Required wiring (minimum, not extra product work):**

1. Browser calls same-origin `/hc-api/...` (`http://localhost:3001/hc-api/health`).
2. `uis/backoffice/next.config.ts` rewrites `/hc-api/:path*` → `${HEALTHCORE_API_INTERNAL_URL}/:path*` (`http://api:8001`).
3. That rewrite target is the inter-service URL and **must** use service name `api`.
4. `docker-compose.yml` must **not** set UI→API URLs to `localhost` or `127.0.0.1`.

Do not add this proxy to `uis/healthcore`. The public site does not call FastAPI.

The only allowed application-code edit for this ticket is that backoffice rewrite (keep existing `turbopack.root` at the monorepo root per PLAN-038).

### Environment (root `.env` only)

Compose: `env_file: .env` on **both** services. Do not hardcode secrets under `environment:`.

`HEALTHCORE_API_INTERNAL_URL=http://api:8001` is a DNS name, not a credential.

**API names** (values only in `.env`):

- `JWT_SECRET_KEY` (required by `Settings`)
- `DATABASE_URL` (required; never commit a live password)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`)
- `RESET_TOKEN_EXPIRE_MINUTES` (default `30`)
- `BACKOFFICE_PUBLIC_URL` (`http://localhost:3001`)
- Optional provider keys — omit for demo mode; **never** put them in YAML

**UI names:**

- `HEALTHCORE_API_INTERNAL_URL=http://api:8001`
- `NEXT_PUBLIC_AUTH_API_URL=/hc-api`
- `NEXT_PUBLIC_SUPPLIERS_API_URL=/hc-api`
- `NEXT_PUBLIC_INCIDENTS_API_URL=/hc-api`
- `NEXT_PUBLIC_INVENTORY_API_URL=/hc-api`
- `WATCHPACK_POLLING=true`
- `CHOKIDAR_USEPOLLING=true`

Root `.gitignore` already lists `.env` and `.env.example`. Confirm: `git check-ignore -v .env`.

### Isolation and privacy

- Do not share Next layouts between `uis/healthcore` and `uis/backoffice`.
- Do not log tokens, `DATABASE_URL`, or PHI.
- Do not commit `.env*`, TinyDB dumps, or live connection strings.

### Hot reload bind mounts

UI:

- `./uis/healthcore` and `./uis/backoffice` onto the paths `start.sh` uses
- `./src` onto `/workspace/src` (backoffice `@hc`)
- Named volumes for each app’s `node_modules` so Windows host modules do not overwrite Alpine installs

API:

- `./services/api` onto the workdir that contains `app/`
- Uvicorn `--reload --host 0.0.0.0 --port 8001`

In-container layout:

```text
/workspace/uis/healthcore
/workspace/uis/backoffice
/workspace/src
```

### CORS

Do **not** change CORS for this ticket. Keep host origins `http://localhost:3001` and `http://127.0.0.1:3001`. Same-origin `/hc-api` does not need `http://ui:3001`.

---

## Developer steps (implementation)

Agents implementing Docker follow this order. Humans **running** the stack after merge use [How to run after implementation](#how-to-run-after-implementation).

1. Confirm Docker Desktop (or Engine + Compose v2) is installed — needed to **verify**, not to author the files.
2. Confirm `.gitignore` lists `.env`. Never commit it.
3. Create root `.env` with the **names** in the table above (placeholder values only in chat/docs).
4. Add `uis/Dockerfile`, `uis/start.sh` (LF), `uis/.dockerignore`.
5. Add `services/Dockerfile`, `services/.dockerignore`. Copy `api/requirements.txt`; workdir is the FastAPI app.
6. Add root `docker-compose.yml`: services `ui` + `api`, network `healthcore`, bind mounts including `./src`, `env_file: .env`, ports 3000/3001/8001, **no secrets**.
7. Add the backoffice `/hc-api` rewrite only. Do not restyle apps or change API routes.
8. Verify with `docker compose up --build` and the test cases below.
9. Stamp a **new** implementation plan. Do not rewrite PLAN-039.

---

## What to build

### 1. `uis/Dockerfile`

- `FROM` official Node **Alpine** (20 or 22).
- `libc6-compat` if Next needs it on Alpine.
- Install **both** `healthcore` and `backoffice` dependencies.
- `CMD` **must** invoke `start.sh`.

### 2. `uis/start.sh`

- Start healthcore: `npm run dev -- --hostname 0.0.0.0 --port 3000` (background).
- Start backoffice: `npm run dev -- --hostname 0.0.0.0 --port 3001` (background).
- `wait` so the container stays up.
- LF line endings.

Compose may set `command` to `start.sh`; it must still start **both** apps.

### 3. `uis/.dockerignore`

At minimum: `node_modules`, `.next`, `.env*`, `*.log`.

### 4. `services/Dockerfile`

- Official Python (3.12 recommended).
- Install `uv`, then `uv pip install "-r" requirements.txt` (add `--system` or a venv if the official image has no venv).
- `COPY api/requirements.txt` then the `api/` tree.
- `uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`

Do **not** require a second `services/start.sh` or `seed.py` on boot for this ticket.

### 5. `services/.dockerignore`

At minimum: `tests`, `.env*`, `*.log`, `__pycache__`, `*.pyc`.

### 6. Root `docker-compose.yml`

- Services `ui` and `api`.
- `env_file: .env`.
- Bind mounts as locked above.
- Ports `3000:3000`, `3001:3001`, `8001:8001`.
- Network `healthcore`.
- `depends_on` is allowed (healthcheck optional, recommended).
- **Zero** passwords, tokens, or API keys in this file.

### 7. Backoffice rewrite (allowed app edit)

Rewrite `/hc-api` → `HEALTHCORE_API_INTERNAL_URL` (default `http://api:8001`). Do not move `turbopack.root` to `uis/backoffice`. Do not import backoffice auth into `uis/healthcore`.

---

## Easy-to-miss requirements

1. Ticket folder `website` = **`healthcore`**.
2. `requirements.txt` is `services/api/requirements.txt`; Dockerfile is still `services/Dockerfile`.
3. Browser `localhost` ≠ inter-service `api`.
4. Bind-mount `src/` or `@hc` breaks in Docker.
5. Listen on `0.0.0.0`, not `127.0.0.1`.
6. Windows: polling env vars + LF on `start.sh`.
7. Node Alpine images usually have **no `wget`/`ping`** — inter-service checks must use `node` or the `api` Python image.
8. Create `.env` first. Never commit it.

---

## Samples

Placeholder values only. **Do not** paste live JWT keys or database passwords into the repo.

### Sample root `.env` (local, gitignored)

```env
# Inter-service (UI container → API container)
HEALTHCORE_API_INTERNAL_URL=http://api:8001

# Browser same-origin proxy (not a secret)
NEXT_PUBLIC_AUTH_API_URL=/hc-api
NEXT_PUBLIC_SUPPLIERS_API_URL=/hc-api
NEXT_PUBLIC_INCIDENTS_API_URL=/hc-api
NEXT_PUBLIC_INVENTORY_API_URL=/hc-api

WATCHPACK_POLLING=true
CHOKIDAR_USEPOLLING=true

# API — replace locally; never commit real values
JWT_SECRET_KEY=replace-me-with-a-long-local-dev-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
RESET_TOKEN_EXPIRE_MINUTES=30
BACKOFFICE_PUBLIC_URL=http://localhost:3001
DATABASE_URL=postgresql://USER:PASSWORD@HOST:6543/postgres
```

A local file SQLite URL may go in **this same `.env`** (not in YAML) if the squad is not using live Supabase, for example `sqlite:////app/data/inventory.db`.

### Sample `uis/.dockerignore`

```text
**/node_modules
**/.next
**/.env
**/.env.*
**/*.log
```

### Sample `services/.dockerignore`

```text
**/tests
**/.env
**/.env.*
**/*.log
**/__pycache__
**/*.pyc
```

### Sample `uis/start.sh`

```sh
#!/bin/sh
set -e
cd /workspace/uis/healthcore
npm run dev -- --hostname 0.0.0.0 --port 3000 &
cd /workspace/uis/backoffice
npm run dev -- --hostname 0.0.0.0 --port 3001 &
wait
```

### Sample `uis/Dockerfile` (structure)

```dockerfile
FROM node:22-alpine
RUN apk add --no-cache libc6-compat
WORKDIR /workspace/uis
COPY healthcore/package.json healthcore/package-lock.json ./healthcore/
COPY backoffice/package.json backoffice/package-lock.json ./backoffice/
RUN cd healthcore && npm ci
RUN cd backoffice && npm ci
COPY start.sh /workspace/uis/start.sh
RUN chmod +x /workspace/uis/start.sh
EXPOSE 3000 3001
CMD ["/workspace/uis/start.sh"]
```

### Sample `services/Dockerfile` (structure)

```dockerfile
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY api/requirements.txt /app/requirements.txt
RUN uv pip install --system "-r" requirements.txt
COPY api/ /app
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

### Sample `docker-compose.yml` (no secrets)

```yaml
services:
  api:
    build:
      context: ./services
      dockerfile: Dockerfile
    env_file:
      - .env
    ports:
      - "8001:8001"
    volumes:
      - ./services/api:/app
    networks:
      - healthcore
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health')"]
      interval: 10s
      timeout: 3s
      retries: 10

  ui:
    build:
      context: ./uis
      dockerfile: Dockerfile
    env_file:
      - .env
    ports:
      - "3000:3000"
      - "3001:3001"
    volumes:
      - ./uis/healthcore:/workspace/uis/healthcore
      - ./uis/backoffice:/workspace/uis/backoffice
      - ./src:/workspace/src
      - ui_healthcore_node_modules:/workspace/uis/healthcore/node_modules
      - ui_backoffice_node_modules:/workspace/uis/backoffice/node_modules
    command: ["/workspace/uis/start.sh"]
    depends_on:
      api:
        condition: service_healthy
    networks:
      - healthcore

networks:
  healthcore:
    name: healthcore

volumes:
  ui_healthcore_node_modules:
  ui_backoffice_node_modules:
```

`127.0.0.1` in the **api** healthcheck is loopback **inside** the api container. It is not an inter-service URL. The UI container must use `http://api:8001`.

### Sample Next rewrite (backoffice)

```ts
async rewrites() {
  const internal =
    process.env.HEALTHCORE_API_INTERNAL_URL?.replace(/\/$/, "") ||
    "http://api:8001";
  return [{ source: "/hc-api/:path*", destination: `${internal}/:path*` }];
},
```

Keep existing `turbopack.root` at the monorepo root.

### Sample host checks

```powershell
Invoke-WebRequest http://localhost:3000 | Select-Object StatusCode
Invoke-WebRequest http://localhost:3001 | Select-Object StatusCode
Invoke-RestMethod http://localhost:8001/health
# expected health: { "status": "ok" }
```

### Sample **inter-service** check (service name)

Node Alpine may not include `wget` or `ping`. Use Node inside `ui`, or Python inside `api`:

```powershell
docker compose exec ui node -e "fetch('http://api:8001/health').then(r=>r.text()).then(console.log)"
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('http://api:8001/health').read().decode())"
```

```bash
docker compose exec ui node -e "fetch('http://api:8001/health').then(r=>r.text()).then(console.log)"
```

Expected body: `{"status":"ok"}`. Fail the rubric if the only working URL from the `ui` container is `http://localhost:8001`.

```powershell
docker network inspect healthcore
```

Both `ui` and `api` must be on network `healthcore`.

### Sample login via proxy (synthetic; not PHI)

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:3001/hc-api/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"ops.manager@healthcore.example","password":"StaffPass9"}'
```

The Next server in `ui` must forward to `http://api:8001/auth/login`. Chrome resolving `http://api:8001` is expected to fail.

### Sample hot-reload probes

- Edit `uis/healthcore/app/page.tsx` on the host → http://localhost:3000 updates without rebuild.
- Edit `uis/backoffice` on the host → http://localhost:3001 updates without rebuild.
- Edit `services/api/app/main.py` on the host → Uvicorn `--reload`; http://localhost:8001/health still 200.

### Sample secret scan

```powershell
Select-String -Path docker-compose.yml,uis/Dockerfile,services/Dockerfile -Pattern "password=|API_KEY=|JWT_SECRET_KEY=\S+"
```

No live values. Env **names** in docs are fine; `JWT_SECRET_KEY=actual-secret` in Git is not.

---

## Test cases

Run from the repository root after `.env` exists. Do not invent PHI.

**Rubric / ticket cases** (must pass for `#infra-40`):

| ID | Type | Action | Expected |
|----|------|--------|----------|
| TC-C01 | Happy | `docker compose up --build` | `ui` and `api` start |
| TC-C02 | Happy | GET http://localhost:3000 | Public site HTTP 200 |
| TC-C03 | Happy | GET http://localhost:3001 | Backoffice HTTP 200 |
| TC-C04 | Happy | GET http://localhost:8001/health | `{"status":"ok"}` |
| TC-C05 | Happy | From `ui`: fetch `http://api:8001/health` | `{"status":"ok"}` |
| TC-C06 | Happy | `docker network inspect healthcore` | Both services on `healthcore` |
| TC-C07 | Happy | Host edit under `uis/healthcore` | Browser updates without rebuild |
| TC-C08 | Happy | Host edit under `uis/backoffice` | Browser updates without rebuild |
| TC-C09 | Happy | Host edit under `services/api/app` | Uvicorn reloads; `/health` 200 |
| TC-C10 | Happy | Read `start.sh` / `CMD` | Both apps; ports 3000 and 3001; **one** `ui` container |
| TC-C11 | Happy | Read `uis/.dockerignore` | `node_modules`, `.next`, `.env*`, `*.log` |
| TC-C12 | Happy | Read `services/.dockerignore` | `tests`, `.env*`, `*.log`, `__pycache__`/`*.pyc` |
| TC-C13 | Happy | `git check-ignore -v .env` | `.env` ignored |
| TC-C14 | Happy | `git ls-files .env docker-compose.yml` | `.env` untracked; Compose tracked |
| TC-C15 | Failure | Grep Compose UI env for `localhost` as API host | No `http://localhost:8001` as inter-service URL |
| TC-C16 | Failure | Grep Compose + Dockerfiles for secrets | No live passwords, JWT values, or provider keys |
| TC-C17 | Failure | Two UI services or a single Next port | Reject |
| TC-C18 | Failure | Compose command is production `next start` without bind mounts | Reject if hot reload fails |

**HealthCore smoke (must not break; do not build new features for these):**

| ID | Action | Expected |
|----|--------|----------|
| TC-C19 | Open http://localhost:3000 | No backoffice chrome, no login wall, no inventory |
| TC-C20 | Open http://localhost:3001/inventory logged out | Existing `AuthGuard` → `/login` (already built) |
| TC-C21 | Host POST `/hc-api/auth/login` with a synthetic user | Proxy reaches `api` (200 or 401 — not DNS failure) |
| TC-C22 | Missing `.env` or empty `JWT_SECRET_KEY` | Must not start with a **committed** default secret |

Do not add pytest/Jest jobs to Compose. Do not add a custom 502 error page for this ticket.

---

## What we will evaluate

Official `#infra-40` list:

- `docker compose up` from the repository root starts the full platform without extra steps beyond a local gitignored `.env`.
- Host code changes appear without rebuilding (bind mounts on **both** services).
- One UI container runs both Next.js apps on **3000** and **3001**.
- Services communicate internally by Docker **service name**, not localhost or a hardcoded IP.
- No secrets, API keys, or passwords hardcoded in any Dockerfile or in `docker-compose.yml`.
- `.env` is in `.gitignore` and does not appear in commit history.
- `.dockerignore` files exist in `/uis` and in `services/`.

### HealthCore mapping (same ticket, this repo)

- [ ] `website` → `uis/healthcore`
- [ ] FastAPI is `services/api` on **8001**
- [ ] `/hc-api` rewrite target is `http://api:8001`
- [ ] `./src` is mounted
- [ ] Public and backoffice layouts stay isolated
- [ ] No `.env` committed

---

## Agent instructions

1. Read this CONTEXT before adding Docker files. Map `website` → `uis/healthcore`.
2. Stay inside [In scope](#in-scope-ticket-infra-40-only). Do not seed on boot, add services, or restyle UIs.
3. Create root `.env` first (gitignored). No secrets in YAML/Dockerfiles.
4. Add the six ticket files plus `uis/start.sh` and the backoffice rewrite.
5. Services `ui` + `api` on network `healthcore`. Internal API URL `http://api:8001`.
6. Bind-mount both apps **and** `src/`. Dev servers on `0.0.0.0`.
7. After shipping Docker files, append a new stamp. Do not rewrite PLAN-039 or this CONTEXT without human confirmation.
8. PHI-safe commits: no patient names, member IDs, clinical free text, passwords, or tokens.

---

## How to run after implementation

Use this section **after** Dockerfiles and `docker-compose.yml` exist. You do not need Node or Python installed on the laptop for this path.

### 1. Download and install Docker Desktop

This repo is typically run on **Windows**. Docker Desktop includes the engine and Compose v2.

1. Open the official installer page: [Install Docker Desktop on Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
2. Download **Docker Desktop for Windows**.
3. Run the installer. Keep **Use WSL 2 instead of Hyper-V** checked when offered (required on current Windows).
4. Finish the installer. Reboot if Windows asks.
5. If WSL 2 is missing, Windows may prompt to install it. Accept, then reboot, then start Docker Desktop again.
6. Launch **Docker Desktop** from the Start menu.
7. Complete the first-run screens (account can be skipped for local use if the app allows).
8. Wait until the whale icon in the system tray shows the engine is **running**. Do not run Compose while it still says “starting”.

macOS / Linux: install Docker Desktop or Engine + the Compose v2 plugin from [Docker’s install docs](https://docs.docker.com/get-started/get-docker/). Then the same `docker compose` commands apply.

### 2. Confirm the engine and Compose

Open **PowerShell** (or Terminal):

```powershell
docker version
docker compose version
```

You should see a Client **and** a Server (Engine). If Server is missing, Docker Desktop is not running — start it and retry.

Compose **v2** is the `docker compose` plugin (space, not `docker-compose` hyphen). The ticket expects v2.

### 3. Open this repository

```powershell
cd C:\Work\Git\Containerization\HealthCore-Venkata-mi-ai-2
```

Use your actual clone path if it differs.

### 4. Create the root `.env` (once per machine)

Compose reads **only** this file for secrets and URLs. It is gitignored. **Do not** `git add .env`.

Create `.env` in the repo root (same folder as `docker-compose.yml`) using the [sample `.env`](#sample-root-env-local-gitignored). Set real `JWT_SECRET_KEY` and `DATABASE_URL` locally. Leave `HEALTHCORE_API_INTERNAL_URL=http://api:8001`.

```powershell
git check-ignore -v .env
# expected: .gitignore mentions .env
```

If `git check-ignore` prints nothing, stop and fix `.gitignore` before Compose.

### 5. Start the full platform

From the **repository root**:

```powershell
docker compose up --build
```

First build downloads Node and Python images and runs `npm ci` / `uv pip install`. That can take several minutes. Leave this terminal open.

Ready when logs show roughly:

- API: Uvicorn running on `0.0.0.0:8001` (reload on)
- UI: Next.js ready on ports **3000** and **3001**

To run in the background instead:

```powershell
docker compose up --build -d
docker compose logs -f
```

### 6. Open the apps (host browser)

Docker Desktop only **runs** the containers (`ui` and `api`). You do **not** browse the HealthCore site inside Docker Desktop. Leave Compose running (do not Ctrl+C yet). Then open a normal browser (Chrome / Edge) with **http** localhost URLs on this PC:

| What | URL |
|------|-----|
| Public HealthCore site | http://localhost:3000 |
| Backoffice (login) | http://localhost:3001 |
| API docs (easiest API check) | http://localhost:8001/docs |
| API health (JSON) | http://localhost:8001/health |

Ready when Compose logs show Uvicorn on `0.0.0.0:8001` and both Next.js apps **Ready** on **3000** and **3001**. You should also see both containers running in Docker Desktop.

**`/health` may look like a blank page.** That is normal. The API returns JSON (`{"status":"ok"}`), not HTML. Confirm with **Ctrl+U** (View Source), **F12 → Network → health → Response**, http://localhost:8001/docs, or:

```powershell
Invoke-RestMethod http://localhost:8001/health
```

Ignore Compose lines like `GET /json/version 404` (Docker Desktop probing). A backoffice `401` then `/login` is expected when you are not signed in.

Sign in on backoffice `/login` the same way as today. Inventory still follows the inventory CONTEXT. The public site must stay unauthenticated.

### 7. Confirm containers talk by **service name**

```powershell
docker compose ps
docker compose exec ui node -e "fetch('http://api:8001/health').then(r=>r.text()).then(console.log)"
docker network inspect healthcore
```

Health from inside `ui` must use host **`api`**, not `localhost`.

### 8. Confirm hot reload (no rebuild)

Edit a visible string on the host under `uis/healthcore` or `uis/backoffice`, then refresh the browser. Edit a Python file under `services/api/app` and confirm Uvicorn reloads. Do **not** run `docker compose build` for ordinary code edits.

### 9. Stop

In the Compose terminal: `Ctrl+C`, then:

```powershell
docker compose down
```

Add `-v` only if you intend to delete the named `node_modules` volumes (next `up --build` will reinstall them).

### 10. If something fails

| Symptom | What to do |
|---------|------------|
| `docker` is not recognized | Start Docker Desktop; open a **new** terminal so PATH reloads; or add `...\DockerDesktop\resources\bin` to PATH |
| Docker Desktop: “Virtualization support not detected” | Enable **Virtual Machine Platform** + **Windows Subsystem for Linux**, reboot; if it persists, enable Intel VT-x in BIOS |
| `error during connect` / cannot find engine | Start Docker Desktop; wait until it is running; retry `docker version` |
| http://localhost:8001/health looks blank | Expected for JSON — use View Source, `/docs`, or `Invoke-RestMethod` |
| `bind: address already in use` on 3000, 3001, or 8001 | Stop the host `npm run dev` / `uvicorn` still using that port, then `docker compose up` again |
| API exits on missing settings | Root `.env` is missing or incomplete (`JWT_SECRET_KEY`, `DATABASE_URL`) |
| Public site or backoffice unreachable | Confirm `start.sh` bound `0.0.0.0`, not `127.0.0.1`; wait for both Next processes |
| Login “failed to fetch” / `api` in the browser | Browser must use `/hc-api` or `localhost:3001`; only containers use `http://api:8001` |
| Backoffice `@hc` import errors | `./src` bind mount is missing |
| `wget: not found` in `ui` | Expected on Node Alpine — use the `node -e "fetch(...)"` check |

Host `pytest` / `npm test` are **not** part of this ticket’s run path.

---

## Do not repeat

- Do not create `uis/website`.
- Do not put `localhost` as the host in UI→API **container** URLs.
- Do not put secrets in `docker-compose.yml` or Dockerfiles.
- Do not commit `.env`.
- Do not drop the `src/` bind mount.
- Do not use production `next start` as the default Compose command.
- Do not add seed-on-boot, extra Compose services, or new error-handling pages for this ticket.
- Do not rewrite inventory/auth CONTEXTs or root `CONTEXT.md`.
- Do not point `turbopack.root` at `uis/backoffice` only.
