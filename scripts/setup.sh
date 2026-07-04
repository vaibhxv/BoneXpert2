#!/usr/bin/env bash
# ============================================================================
# One-shot setup: Python engine (venv + deps + model download) and Node apps.
# Usage:  bash scripts/setup.sh
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON_BIN:-python3}"

echo "==> [1/3] Python inference engine (bone-age-ai)"
cd "$ROOT/bone-age-ai"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

if [ ! -e models/bone-age/current ] || [ ! -e models/crop/current ]; then
  echo "==> Downloading models (one-time, requires internet)"
  ./.venv/bin/python scripts/download_models.py
else
  echo "==> Models already present, skipping download."
fi

echo "==> [2/3] NestJS API gateway (api)"
cd "$ROOT/api"
npm install

echo "==> [3/3] Web UI (web)"
cd "$ROOT/web"
npm install

cd "$ROOT"
echo ""
echo "Setup complete."
echo "  Dev:   make dev     (engine + API + web with hot reload)"
echo "  Prod:  make deploy  (build + run under pm2)"
