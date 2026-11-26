#!/usr/bin/env bash
# Start SMIT so that OTHER computers on the SAME network (Wi-Fi/LAN) can open it.
# The data are still stored only on THIS computer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${SMIT_PORT:-8000}"

# Safety: the dashboard becomes reachable from the network, so the default password is not allowed.
if [ ! -f "$ROOT/.env" ] || grep -qE '^SMIT_ADMIN_PASSWORD=(change-me-now)?\s*$' "$ROOT/.env" || ! grep -q '^SMIT_ADMIN_PASSWORD=' "$ROOT/.env"; then
  echo "Refusing to start in network mode: set your own SMIT_ADMIN_PASSWORD in .env first (see .env.example)."
  exit 1
fi

IPS=""
for IF in en0 en1 en2 en3; do
  ip="$(ipconfig getifaddr "$IF" 2>/dev/null || true)"
  [ -n "$ip" ] && IPS="$IPS $ip"
done
[ -z "$IPS" ] && IPS="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"   # Linux

echo "------------------------------------------------------------------"
echo " SMIT is reachable from other computers on the same network:"
for ip in $IPS; do
  echo "   Participants:  http://$ip:$PORT/participate"
  echo "   Researcher:    http://$ip:$PORT/researcher"
done
echo " On this computer: http://127.0.0.1:$PORT"
echo " If macOS asks 'Allow incoming network connections?' for Python, click ALLOW."
echo " Keep this window open. Press Ctrl+C to stop."
echo "------------------------------------------------------------------"
SMIT_HOST=0.0.0.0 SMIT_PORT="$PORT" exec "$ROOT/scripts/start.sh"
