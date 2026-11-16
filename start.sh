#!/usr/bin/env bash
# Sprintline Issue Tracker — one command, both services.
#
#   backend  : FastAPI + uvicorn on 0.0.0.0:${PORT:-8000}
#   frontend : Vite dev server on 0.0.0.0:${FRONTEND_PORT:-5173}, proxying /api
#
# Stays in the foreground; Ctrl-C stops both. Installs only if a dependency
# tree is completely missing (normally `./install.sh` has already run).
set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-${PORT:-8000}}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

PY="python3"
if [ -x "backend/.venv/bin/python" ]; then
  PY="$PWD/backend/.venv/bin/python"
fi

if ! "$PY" -c "import uvicorn, fastapi, pydantic_settings, jwt, bcrypt" >/dev/null 2>&1; then
  echo "==> Backend dependencies missing — installing"
  PIP_BREAK_SYSTEM_PACKAGES=1 "$PY" -m pip install --no-input -q -r backend/requirements.txt
fi

if [ ! -d frontend/node_modules ]; then
  echo "==> Frontend dependencies missing — installing"
  (cd frontend && npm install --no-audit --no-fund --loglevel=error)
fi

echo "==> Starting Sprintline API on 0.0.0.0:${BACKEND_PORT}"
(cd backend && exec "$PY" -m uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT") &
BACKEND_PID=$!

for _ in $(seq 1 180); do
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
    echo "    API is answering on http://0.0.0.0:${BACKEND_PORT}"
    break
  fi
  sleep 0.5
done

echo "==> Starting Sprintline UI on 0.0.0.0:${FRONTEND_PORT}"
(
  cd frontend
  API_PROXY_TARGET="http://127.0.0.1:${BACKEND_PORT}" FRONTEND_PORT="$FRONTEND_PORT" \
    exec npx vite --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort
) &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait -n "$BACKEND_PID" "$FRONTEND_PID" || true
echo "==> A service exited — shutting the other one down"
