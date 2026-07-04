#!/usr/bin/env bash
# ============================================================================
# Run all three apps in development with hot reload:
#   - Python engine (uvicorn)      :8000
#   - NestJS API (watch)           :3000
#   - Vite dev server (UI)         :5173  (proxies /api -> :3000)
# Ctrl-C stops everything.
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

pids=()
cleanup() {
  echo ""
  echo "==> Stopping..."
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Engine  http://localhost:8000"
( cd "$ROOT/bone-age-ai" && exec ./.venv/bin/python -m app.main ) &
pids+=("$!")

echo "==> API     http://localhost:3000/api"
( cd "$ROOT/api" && exec npm run start:dev ) &
pids+=("$!")

echo "==> UI      http://localhost:5173"
( cd "$ROOT/web" && exec npm run dev ) &
pids+=("$!")

wait
