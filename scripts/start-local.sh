#!/usr/bin/env bash
# Start SentinelFlux locally at http://sentinelflux.in
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. Ensure /etc/hosts entry
if ! grep -q "sentinelflux.in" /etc/hosts; then
  echo "Adding sentinelflux.in to /etc/hosts (requires sudo)..."
  sudo sh -c 'echo "127.0.0.1  sentinelflux.in" >> /etc/hosts'
fi

# 2. Start the dashboard server in the background
echo "Starting SentinelFlux dashboard on port 8765..."
cd "$SCRIPT_DIR"
.venv/bin/python -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8765 &
UVICORN_PID=$!

# Give uvicorn a moment to start
sleep 1

# 3. Start Caddy as reverse proxy (port 80 -> 8765)
echo "Starting Caddy reverse proxy (sentinelflux.in:80 -> 8765)..."
sudo caddy run --config "$SCRIPT_DIR/Caddyfile" &
CADDY_PID=$!

echo ""
echo "  Dashboard: http://sentinelflux.in"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C and kill both processes
trap "echo 'Stopping...'; sudo kill $CADDY_PID 2>/dev/null; kill $UVICORN_PID 2>/dev/null" INT TERM
wait $UVICORN_PID
