#!/usr/bin/env bash
# Start an ISOLATED backend for end-to-end tests (fresh temporary database; never the research DB).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export SMIT_DATA_DIR="${SMIT_E2E_DATA_DIR:-$ROOT/tests/artifacts/e2e_data}"
rm -rf "$SMIT_DATA_DIR"
mkdir -p "$SMIT_DATA_DIR"
export SMIT_ADMIN_PASSWORD="e2e-test-password"
export SMIT_SECRET_KEY="e2e-secret"
export SMIT_ALLOW_SYNTHETIC_IMPORTS="true"
# Headless test browsers are not MacBooks; the computer check is covered by unit tests instead.
export SMIT_REQUIRE_DEVICE_CHECK="false"
cd "$ROOT/backend"
exec "$ROOT/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port "${SMIT_E2E_PORT:-8765}" --log-level warning
