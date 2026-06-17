#!/usr/bin/env bash
# =============================================================================
#  Stop the AirLLM Gateway services started by start-airllm.sh.
#
#  Only AirLLM-OWNED processes are touched: the dev servers are matched by their
#  exact command lines ("uvicorn app.main:app" / "next dev"), never by port, so
#  an unrelated service that happens to use :4000 or :3000 is left untouched.
#
#  Usage:
#    ./stop-airllm.sh                  stop backend + dashboard + Postgres
#    ./stop-airllm.sh --services-only  stop backend + dashboard, keep Postgres
# =============================================================================
set -uo pipefail

SERVICES_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --services-only) SERVICES_ONLY=1 ;;
  esac
done

echo "Stopping AirLLM Gateway services..."

# Best-effort: stop the dev servers if they're still running (AirLLM-owned).
pkill -f "uvicorn app.main:app" >/dev/null 2>&1 && echo "  - Backend stopped." || echo "  - Backend was not running."
pkill -f "next dev" >/dev/null 2>&1 && echo "  - Dashboard stopped." || echo "  - Dashboard was not running."

if [ "$SERVICES_ONLY" = "1" ]; then
  exit 0
fi

# Stop the AirLLM-owned Postgres container (data volume is preserved).
if command -v docker >/dev/null 2>&1; then
  docker stop airllm-pg >/dev/null 2>&1 && echo "  - Postgres container stopped." || echo "  - Postgres container was not running."
fi

echo "Done."
