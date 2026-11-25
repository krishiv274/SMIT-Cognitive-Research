#!/usr/bin/env bash
# One-time setup on macOS / Linux: Python venv, backend dependencies, frontend build.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required"'
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements-dev.txt
(cd frontend && npm ci && npm run build)
[ -f .env ] || { cp .env.example .env; echo "Created .env — EDIT the passwords/secrets before real data collection."; }
echo "Setup complete. Start with: ./scripts/start.sh"
