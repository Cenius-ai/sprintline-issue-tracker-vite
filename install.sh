#!/usr/bin/env bash
# Sprintline Issue Tracker — install step.
#
# Installs project dependencies (Python backend + npm frontend), prepares the
# SQLite workspace and seeds the demo data. It NEVER starts a server: run
# ./start.sh (or the two dev commands in INSTALL.md) afterwards.
set -euo pipefail
cd "$(dirname "$0")"

export PIP_DISABLE_PIP_VERSION_CHECK=1
export npm_config_yes=true
export CI=true

PY="python3"
if [ -x "backend/.venv/bin/python" ]; then
  PY="$PWD/backend/.venv/bin/python"
fi

echo "==> [1/5] Python tooling"
"$PY" -m pip install --no-input --upgrade pip setuptools wheel >/dev/null 2>&1 \
  || echo "    pip tooling already current"

echo "==> [2/5] Backend dependencies (backend/requirements.txt)"
if PIP_BREAK_SYSTEM_PACKAGES=1 "$PY" -m pip install --no-input -r backend/requirements.txt; then
  echo "    Python dependencies installed"
else
  echo "==> System interpreter is not writable — falling back to backend/.venv"
  python3 -m venv backend/.venv
  PY="$PWD/backend/.venv/bin/python"
  "$PY" -m pip install --no-input --upgrade pip >/dev/null
  "$PY" -m pip install --no-input -r backend/requirements.txt
fi

echo "==> [3/5] Frontend dependencies (frontend/package.json)"
(cd frontend && npm install --no-audit --no-fund --loglevel=error)

echo "==> [4/5] backend/.env"
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  SECRET="$("$PY" -c 'import secrets; print(secrets.token_hex(32))')"
  printf 'JWT_SECRET=%s\n' "$SECRET" >> backend/.env
  echo "    wrote backend/.env with a generated JWT secret"
else
  echo "    backend/.env already present — left untouched"
fi

echo "==> [5/5] Seeding the demo workspace"
(cd backend && "$PY" -m seed)

echo "==> Import self-check"
(cd backend && "$PY" -c "import main; print('    backend imports cleanly')")

echo ""
echo "Install complete. Start the app with:"
echo "  ./start.sh              # both services: API on :8000, UI on http://localhost:5173"
echo "Demo login: cenius@cenius.ai / cenius"
