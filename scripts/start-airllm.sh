#!/usr/bin/env bash
# =============================================================================
#  AirLLM Gateway - one-click local startup (Linux / macOS)
#
#  Brings up PostgreSQL (Docker), the gateway on :4000 and the dashboard on
#  :3000. Backend and dashboard share one ADMIN_API_KEY so they agree out of
#  the box.
#
#  IDEMPOTENT: running this multiple times never creates duplicate backend or
#  dashboard processes. A healthy service already on its port is reused, not
#  restarted. Nothing is killed automatically.
#
#  Usage:
#    ./start-airllm.sh             start missing services, reuse healthy ones
#    ./start-airllm.sh --restart   stop AirLLM-owned services, then start fresh
#
#  Ctrl-C stops only the services this invocation started.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- Parse arguments (only --restart is recognised) ---
RESTART=0
for arg in "$@"; do
  case "$arg" in
    --restart) RESTART=1 ;;
  esac
done

# --- Shared admin token (override via environment) ---
export ADMIN_API_KEY="${ADMIN_API_KEY:-changeme-admin-key}"
export BACKEND_INTERNAL_URL="${BACKEND_INTERNAL_URL:-http://localhost:4000}"
if [ "$ADMIN_API_KEY" = "changeme-admin-key" ]; then
  echo "[WARN] Using the default ADMIN_API_KEY. Set a strong value for any non-local use."
fi

# --- Helpers ---------------------------------------------------------------
# True (0) when something is listening on the given TCP port. Uses bash's
# /dev/tcp so it needs no extra tooling (ss/lsof/netstat).
port_in_use() {
  (exec 3<>"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1 && exec 3>&- 3<&-
}

# True (0) when 127.0.0.1:4000/health answers as a healthy AirLLM backend.
backend_healthy() {
  curl -fsS --max-time 3 "http://127.0.0.1:4000/health" >/dev/null 2>&1
}

# --- Optional restart: stop only AirLLM-owned services, keep Postgres up ---
if [ "$RESTART" = "1" ]; then
  echo "[AirLLM] --restart requested: stopping existing AirLLM backend/dashboard..."
  pkill -f "uvicorn app.main:app" >/dev/null 2>&1 || true
  pkill -f "next dev" >/dev/null 2>&1 || true
  sleep 2
fi

# --- 1. PostgreSQL via Docker ---
if command -v docker >/dev/null 2>&1; then
  echo "Starting PostgreSQL container..."
  docker start airllm-pg >/dev/null 2>&1 || docker run --name airllm-pg \
    -e POSTGRES_USER=airllm -e POSTGRES_PASSWORD=airllm -e POSTGRES_DB=airllm \
    -p 5432:5432 -d postgres:16-alpine >/dev/null
else
  echo "[WARN] Docker not found. Assuming PostgreSQL is already running on :5432."
fi
sleep 5

# Pick the right venv layout (POSIX vs Windows-style).
if [ -x "backend/.venv/bin/alembic" ]; then
  VENV_BIN="backend/.venv/bin"
else
  VENV_BIN="backend/.venv/Scripts"
fi

pids=()
cleanup() {
  echo ""
  echo "Stopping AirLLM Gateway (services started by this run)..."
  for pid in "${pids[@]:-}"; do kill "$pid" >/dev/null 2>&1 || true; done
}
trap cleanup INT TERM

# --- 2. Backend on :4000 (reuse if already healthy) ---
if port_in_use 4000; then
  if backend_healthy; then
    echo "[AirLLM] Backend already running on port 4000."
  else
    echo "[WARN] Port 4000 is in use but not a healthy AirLLM backend."
    echo "[WARN] Skipping backend start to avoid a bind conflict; use --restart to replace it."
  fi
else
  echo "Starting gateway backend on :4000 ..."
  ( cd backend && "../$VENV_BIN/alembic" upgrade head \
      && "../$VENV_BIN/uvicorn" app.main:app --host 0.0.0.0 --port 4000 ) &
  pids+=("$!")
fi

# --- 3. Dashboard on :3000 (reuse if already running) ---
if port_in_use 3000; then
  echo "[AirLLM] Dashboard already running on port 3000."
else
  echo "Starting dashboard on :3000 ..."
  ( cd frontend && npm run dev ) &
  pids+=("$!")
fi

# --- 4. Open the browser once, only if we started something ---
if [ "${#pids[@]}" -gt 0 ]; then
  sleep 6
  ( xdg-open http://localhost:3000 >/dev/null 2>&1 \
    || open http://localhost:3000 >/dev/null 2>&1 || true )
fi

# --- 5. Status banner ---
backend_state="Not running"; port_in_use 4000 && backend_state="Running (port 4000)"
dash_state="Not running";    port_in_use 3000 && dash_state="Running (port 3000)"
db_state="Not connected";    port_in_use 5432 && db_state="Connected"

echo ""
echo "===================================="
echo " AirLLM Startup Status"
echo "===================================="
echo "Backend   : $backend_state"
echo "Dashboard : $dash_state"
echo "Database  : $db_state"
echo "===================================="
echo "   Dashboard : http://localhost:3000"
echo "   Gateway   : http://localhost:4000"
echo "   API docs  : http://localhost:4000/docs"

# Foreground-wait only on the services we started; otherwise leave the already
# running stack alone and return.
if [ "${#pids[@]}" -gt 0 ]; then
  echo "Press Ctrl-C to stop the services started by this run."
  wait
else
  echo "All services were already running - nothing to start."
fi
