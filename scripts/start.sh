#!/usr/bin/env bash
# Start SMIT (backend + built frontend) on http://127.0.0.1:8000
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -d "$ROOT/frontend/dist" ] || (cd "$ROOT/frontend" && npm run build)
cd "$ROOT/backend"
HOST="${SMIT_HOST:-127.0.0.1}"
PORT="${SMIT_PORT:-8000}"
echo "SMIT running at http://$HOST:$PORT   (participant: /participate   researcher: /researcher)"
exec "$ROOT/.venv/bin/uvicorn" app.main:app --host "$HOST" --port "$PORT"
