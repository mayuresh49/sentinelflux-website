#!/usr/bin/env bash
# Force Caddy to reload with a clean slate — use when:
#   - Caddyfile was updated but Caddy is still using old config/domain
#   - TLS cert provisioning is stuck or failing for wrong domain
#   - "identifier: sentinelflux.in" appears in logs instead of app.sentinelflux.in
# Run as root on the GCP VM.
set -euo pipefail

APP_DIR="/home/sentinelflux/app"

echo "==> Writing Caddyfile from repo"
cp "${APP_DIR}/scripts/Caddyfile.prod" /etc/caddy/Caddyfile
echo "    Domain: $(grep -v '^#' /etc/caddy/Caddyfile | head -1)"

echo "==> Clearing Caddy autosave + cert cache"
rm -f /home/caddy/.config/caddy/autosave.json
rm -rf /home/caddy/.local/share/caddy/certificates

echo "==> Restarting Caddy"
systemctl restart caddy
sleep 8

echo "==> Caddy status"
journalctl -u caddy -n 20 --no-pager
