#!/usr/bin/env bash
# Run every automated test suite (all use temporary databases; the research DB is never touched).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Backend (pytest)";            (cd "$ROOT/backend" && "$ROOT/.venv/bin/python" -m pytest -q -p no:warnings)
echo "== Frontend unit (vitest)";      (cd "$ROOT/frontend" && npx vitest run)
echo "== Type check + build";          (cd "$ROOT/frontend" && npm run build)
echo "== End-to-end (Playwright)";     (cd "$ROOT/frontend" && npx playwright test)
echo "Optional full-length dry run:   (cd frontend && SMIT_DRY_RUN=1 npx playwright test tests/03_dry_run_default_config.spec.ts)"
