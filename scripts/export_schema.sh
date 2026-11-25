#!/usr/bin/env bash
# Regenerate database/schema/schema_sqlite.sql from the Alembic migrations.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
cd "$ROOT/backend"
SMIT_DATA_DIR="$TMP" "$ROOT/.venv/bin/alembic" upgrade head
sqlite3 "$TMP/smit.db" .schema > "$ROOT/database/schema/schema_sqlite.sql"
rm -rf "$TMP"
echo "Wrote database/schema/schema_sqlite.sql"
