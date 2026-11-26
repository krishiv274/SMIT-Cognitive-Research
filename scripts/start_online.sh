#!/usr/bin/env bash
# Make SMIT reachable from ANY network through a free Cloudflare quick tunnel.
# Data are still stored only on THIS computer; traffic passes through Cloudflare (HTTPS).
# The computer must stay on and this window open. The link changes every time you start.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${SMIT_PORT:-8000}"
LOG="$ROOT/data/tunnel.log"
mkdir -p "$ROOT/data"

command -v cloudflared >/dev/null || { echo "cloudflared is not installed. Run: brew install cloudflared"; exit 1; }
# The researcher dashboard becomes reachable from the internet: defaults are not allowed.
for k in SMIT_ADMIN_PASSWORD SMIT_SECRET_KEY SMIT_EMAIL_PEPPER; do
  v="$(grep -E "^$k=" "$ROOT/.env" 2>/dev/null | head -1 | cut -d= -f2- || true)"
  case "$v" in ""|change-me-now|dev-secret-change-me|change-this-pepper)
    echo "Refusing to go online: set your own $k in .env first (see .env.example)."; exit 1;; esac
done
pw="$(grep -E '^SMIT_ADMIN_PASSWORD=' "$ROOT/.env" | cut -d= -f2-)"
[ "${#pw}" -lt 12 ] && echo "WARNING: your researcher password is short (${#pw} characters). Use 12+ characters for an online study."

# Start the app on this computer only; the tunnel is the only way in from outside.
if ! curl -s "http://127.0.0.1:$PORT/api/health" >/dev/null; then
  SMIT_HOST=127.0.0.1 SMIT_PORT="$PORT" "$ROOT/scripts/start.sh" > "$ROOT/data/server.log" 2>&1 &
  SERVER_PID=$!
  trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
  for _ in $(seq 1 30); do curl -s "http://127.0.0.1:$PORT/api/health" >/dev/null && break; sleep 1; done
fi

# Keep the Mac from sleeping while the study is online (macOS only).
command -v caffeinate >/dev/null && caffeinate -i -w $$ &

: > "$LOG"
cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" > "$LOG" 2>&1 &
TUNNEL_PID=$!
trap 'kill $TUNNEL_PID 2>/dev/null || true; kill ${SERVER_PID:-0} 2>/dev/null || true' EXIT
URL=""
for _ in $(seq 1 60); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1 || true)"
  [ -n "$URL" ] && break
  sleep 1
done
[ -z "$URL" ] && { echo "Could not start the tunnel. Details: $LOG"; exit 1; }

echo "------------------------------------------------------------------"
echo " SMIT is ONLINE (works from any network):"
echo "   Share with participants:  $URL/participate"
echo "   Researcher dashboard:     $URL/researcher"
echo " Keep this computer ON and AWAKE, and keep this window open."
echo " The link changes every time you restart. Press Ctrl+C to stop."
echo "------------------------------------------------------------------"
wait $TUNNEL_PID
