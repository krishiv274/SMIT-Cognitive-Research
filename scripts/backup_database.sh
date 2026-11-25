#!/usr/bin/env bash
# Consistent online backup of the SQLite research database (run after each testing day).
# Store backups on an ENCRYPTED drive and delete them at the end of the retention period.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${SMIT_DATA_DIR:-$ROOT/data}"
DEST="${1:-$ROOT/backups}"
mkdir -p "$DEST"
OUT="$DEST/smit_$(date +%Y%m%d_%H%M%S).db"
sqlite3 "$DATA/smit.db" ".backup '$OUT'"
chmod 600 "$OUT"
echo "Backup written to $OUT"
