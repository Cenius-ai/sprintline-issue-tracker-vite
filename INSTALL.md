# Installing Sprintline

Sprintline is a two-service app: a FastAPI backend in `backend/` and a Vite React frontend in
`frontend/`. Each has its own manifest; this document is the source of truth for bringing the whole
thing up.

## Prerequisites

| Tool     | Version          | Notes                                              |
| -------- | ---------------- | -------------------------------------------------- |
| Python   | 3.11 or newer    | `python3` and `pip3` on `PATH`                     |
| Node.js  | 20 or newer      | ships `npm` 10                                     |
| npm      | 10 or newer      | the frontend's committed lockfile is `package-lock.json` — use **npm**, not yarn or pnpm |

No database server is needed: persistence is a SQLite file the app creates for itself. No
`sudo`, no system packages, no container runtime.

## Step 1 — Install dependencies

```bash
bash install.sh
```

This is idempotent and does exactly four things, then exits:

1. installs `backend/requirements.txt` with pip (and `frontend/package-lock.json` with
   `npm install --no-audit --no-fund`);
2. writes `backend/.env` with a freshly generated `JWT_SECRET` if that file does not exist yet;
3. runs the idempotent seed;
4. imports the backend once as a self-check.

Prefer doing it by hand? Run the two installs yourself:

```bash
# backend
cd backend
PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install -r requirements.txt
cd ..

# frontend (npm only — package-lock.json is committed)
cd frontend
npm install --no-audit --no-fund
cd ..
```

On Debian/Ubuntu images pip may refuse to write to the system environment (PEP 668). Either keep
`PIP_BREAK_SYSTEM_PACKAGES=1` as above, or create a virtualenv first — `install.sh` detects
`backend/.venv` and uses it automatically.

## Step 2 — Seed the demo workspace

```bash
cd backend
python3 -m seed
cd ..
```

Creates the demo login `cenius@cenius.ai` / `cenius` (bcrypt-hashed through the app's own code path),
three teammates, two projects, three sprint cycles, six labels, 24 issues, 11 comments and the full
activity history. It never starts the HTTP server and never duplicates rows: re-running prints
`workspace already seeded — nothing to do`.

The API also seeds itself on the normal boot path when the database is empty, so a fresh clone with
no seed step still boots populated.

## Step 3 — Run it in development

Both services, one command:

```bash
./start.sh
```

- API: <http://localhost:8000> (`/docs` for OpenAPI, `/api/health` for the probe)
- UI: <http://localhost:5173> — the Vite dev server proxies `/api` to the API

Sign in at <http://localhost:5173/login> with `cenius@cenius.ai` / `cenius`.

Or in two terminals, which is what the individual services do anyway:

```bash
# terminal 1 — API on 0.0.0.0:8000
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# terminal 2 — Vite dev server on 0.0.0.0:5173, proxying /api → :8000
cd frontend
npm run dev
```

Ports come from the environment: `PORT`/`BACKEND_PORT` for the API and `FRONTEND_PORT` for the UI.
`API_PROXY_TARGET` overrides the proxy target when the API is not on port 8000.

## Step 4 — Run the tests

```bash
python3 -m pytest          # from the repo root (pytest.ini points at backend/tests)
```

The suite uses a temporary SQLite database seeded once per session. No network, no external
services, no interactive prompts.

## Step 5 — Production build (optional)

```bash
cd frontend
npm run build              # type-checks with tsc, then bundles to frontend/dist
```

`npm run preview` serves the built bundle on port 5173 for a quick check. In production you would put
`frontend/dist` behind any static file server and reverse-proxy `/api` to the FastAPI process; CORS
is configured for both the proxied (same-origin) and direct-API cases.

## Configuration

All backend settings are optional — the service boots with no `.env` at all.

| Variable                 | Default                | Purpose                                              |
| ------------------------ | ---------------------- | ---------------------------------------------------- |
| `SPRINTLINE_DATABASE_URL`| `sqlite:///./app.db`    | SQLAlchemy URL; relative SQLite file by default      |
| `JWT_SECRET`             | dev fallback in code   | HS256 signing key; `install.sh` generates a real one |
| `JWT_EXPIRE_MINUTES`     | `720`                  | Session lifetime                                     |
| `CORS_ORIGINS`           | `*`                    | Comma-separated allowlist, or `*` for dev            |
| `AUTO_SEED`              | `true`                 | Seed the workspace on boot when the database is empty|

Frontend: `API_PROXY_TARGET` (proxy target) and `FRONTEND_PORT` (dev server port) — both optional.

## Troubleshooting

| Symptom                                        | Fix                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------- |
| `externally-managed-environment` from pip      | `export PIP_BREAK_SYSTEM_PACKAGES=1` or use `install.sh` (it detects and falls back to `backend/.venv`) |
| Login returns 401 for the demo credentials     | Run the seed in `backend/`: `python3 -m seed`                       |
| `ECONNREFUSED` from the UI, `/api/health` 502  | The API is not running on port 8000 — start it or set `API_PROXY_TARGET` |
| `sh: 1: vite: not found`                       | `cd frontend && npm install`                                        |
| Stale data after changing models               | Delete `backend/app.db*` and restart; the boot path re-creates and seeds |
