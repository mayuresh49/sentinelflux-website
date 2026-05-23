#!/usr/bin/env bash
# Pull latest code and restart the dashboard service.
# Run as the sentinelflux user: bash scripts/deploy.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${APP_DIR}"

echo "==> Pulling latest code"
# SSH config in ~/.ssh/config routes github.com through the deploy key automatically
GIT_SSH_COMMAND="ssh -i ~/.ssh/sentinelflux_deploy -o IdentitiesOnly=yes" git pull origin main

echo "==> Updating dependencies"
.venv/bin/pip install --quiet -e '.[all]'

echo "==> Restarting service"
sudo systemctl restart sentinelflux

echo "Deployed $(git rev-parse --short HEAD)"
