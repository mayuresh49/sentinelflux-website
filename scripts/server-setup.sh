#!/usr/bin/env bash
# One-shot bootstrap for a fresh Hetzner Ubuntu 24.04 server.
# Run as root: bash scripts/server-setup.sh
set -euo pipefail

REPO="https://github.com/mayuresh49/sentinelflux.git"
APP_USER="sentinelflux"
APP_DIR="/home/${APP_USER}/app"
PYTHON="python3.12"

echo "==> Installing system packages"
apt-get update -qq
apt-get install -y git "${PYTHON}" "${PYTHON}-venv" python3-pip ufw curl

echo "==> Installing Caddy"
curl -fsSL https://caddyserver.com/install.sh | bash

echo "==> Configuring firewall"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> Creating app user"
id -u "${APP_USER}" &>/dev/null || useradd -m -s /bin/bash "${APP_USER}"

echo "==> Cloning repo"
if [ ! -d "${APP_DIR}" ]; then
    git clone "${REPO}" "${APP_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
fi

echo "==> Creating virtualenv and installing dependencies"
sudo -u "${APP_USER}" bash -c "
    cd ${APP_DIR}
    ${PYTHON} -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -e '.[all]'
"

echo "==> Installing Playwright browsers"
sudo -u "${APP_USER}" bash -c "
    cd ${APP_DIR}
    .venv/bin/playwright install chromium --with-deps
"

echo "==> Installing systemd service"
cp "${APP_DIR}/scripts/sentinelflux.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable sentinelflux

echo "==> Configuring Caddy"
cp "${APP_DIR}/scripts/Caddyfile.prod" /etc/caddy/Caddyfile
systemctl enable caddy

echo ""
echo "Setup complete. Before starting services:"
echo ""
echo "  1. Copy and fill in the env file:"
echo "       cp ${APP_DIR}/.env.example ${APP_DIR}/.env"
echo "       nano ${APP_DIR}/.env"
echo ""
echo "  2. Seed the first admin user:"
echo "       sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python ${APP_DIR}/scripts/seed_admin.py \\"
echo "           --email your@email.com --password yourpassword"
echo ""
echo "  3. Start services:"
echo "       systemctl start sentinelflux caddy"
echo ""
echo "  4. Check status:"
echo "       systemctl status sentinelflux"
echo "       journalctl -u sentinelflux -f"
