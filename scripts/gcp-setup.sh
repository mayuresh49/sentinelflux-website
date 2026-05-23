#!/usr/bin/env bash
# Bootstrap a fresh GCP VM (Debian 13 / Ubuntu 24.04) for SentinelFlux dashboard.
# Run as root: bash scripts/gcp-setup.sh
#
# What this does vs server-setup.sh:
#   - Uses python3/python3-venv (Debian 13 ships Python 3.13 as plain python3)
#   - Installs Caddy via apt (cloudsmith repo) — not the shell installer which fails on Debian 13
#   - Creates /home/caddy dirs so Caddy can store Let's Encrypt certs
#   - Adds 512 MB swap (e2-micro has only 1 GB RAM)
#   - Generates SSH deploy key ON the VM — prints public key for GitHub
#   - Installs deps from requirements.txt (more reliable than pip install -e '.[all]')
#   - Skips Playwright install (use remote runner for Playwright-based tests)
#   - Caddy auto-provisions TLS for app.sentinelflux.in via Let's Encrypt
set -euo pipefail

REPO="git@github.com:mayuresh49/sentinelflux-app.git"
APP_USER="sentinelflux"
APP_DIR="/home/${APP_USER}/app"
DEPLOY_KEY="/home/${APP_USER}/.ssh/sentinelflux_deploy"

echo "==> Installing system packages"
apt-get update -qq
apt-get install -y git python3 python3-venv python3-pip ufw curl \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2

echo "==> Adding 512 MB swap (safety net for WeasyPrint PDF spikes)"
if [ ! -f /swapfile ]; then
    fallocate -l 512M /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Installing Caddy (via apt — shell installer fails on Debian 13)"
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -qq
apt-get install -y caddy

echo "==> Creating Caddy home dirs for TLS cert storage"
mkdir -p /home/caddy/.local/share/caddy /home/caddy/.config/caddy
chown -R caddy:caddy /home/caddy

echo "==> Configuring firewall"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> Creating app user"
id -u "${APP_USER}" &>/dev/null || useradd -m -s /bin/bash "${APP_USER}"

echo "==> Setting up SSH deploy key"
mkdir -p "/home/${APP_USER}/.ssh"
chmod 700 "/home/${APP_USER}/.ssh"

if [ ! -f "${DEPLOY_KEY}" ]; then
    ssh-keygen -t ed25519 -f "${DEPLOY_KEY}" -N "" -C "sentinelflux-gcp-vm"
    echo ""
    echo "  ============================================================"
    echo "  Add this deploy key to github.com/mayuresh49/sentinelflux-app"
    echo "  Settings → Deploy Keys → Add deploy key (read-only)"
    echo ""
    cat "${DEPLOY_KEY}.pub"
    echo "  ============================================================"
    echo ""
    read -rp "  Press Enter after adding the key to GitHub..."
fi

# SSH config so git uses the deploy key for github.com
SSH_CONFIG="/home/${APP_USER}/.ssh/config"
if ! grep -q "sentinelflux_deploy" "${SSH_CONFIG}" 2>/dev/null; then
    cat >> "${SSH_CONFIG}" <<EOF

Host github.com
    HostName github.com
    User git
    IdentityFile ${DEPLOY_KEY}
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
EOF
fi

chown -R "${APP_USER}:${APP_USER}" "/home/${APP_USER}/.ssh"
chmod 600 "${SSH_CONFIG}"

echo "==> Cloning private repo"
if [ ! -d "${APP_DIR}" ]; then
    sudo -u "${APP_USER}" git clone "${REPO}" "${APP_DIR}"
fi

echo "==> Fixing ownership"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "==> Creating virtualenv and installing dependencies"
sudo -u "${APP_USER}" bash -c "
    cd ${APP_DIR}
    python3 -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -r requirements.txt
    .venv/bin/pip install --quiet -e '.[all]'
"

# NOTE: Playwright intentionally NOT installed on this VM.
# A11y, visual regression, and AppExplorer run via the remote runner daemon
# on your local machine: sentinelflux runner --server https://app.sentinelflux.in

echo "==> Installing systemd service"
cp "${APP_DIR}/scripts/sentinelflux.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable sentinelflux

echo "==> Configuring Caddy (app.sentinelflux.in → localhost:8765)"
cp "${APP_DIR}/scripts/Caddyfile.prod" /etc/caddy/Caddyfile
# Clear any stale autosave/cert cache so Caddy uses the new Caddyfile cleanly
rm -f /home/caddy/.config/caddy/autosave.json
rm -rf /home/caddy/.local/share/caddy/certificates
systemctl enable caddy

echo ""
echo "Setup complete. Before starting services:"
echo ""
echo "  1. Copy and fill in the env file:"
echo "       cp ${APP_DIR}/.env.example ${APP_DIR}/.env"
echo "       nano ${APP_DIR}/.env"
echo "       # Required: SECRET_KEY, MISTRAL_API_KEY (or ANTHROPIC_API_KEY)"
echo ""
echo "  2. Seed the first admin user:"
echo "       sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python ${APP_DIR}/scripts/seed_admin.py \\"
echo "           --email your@email.com --password yourpassword"
echo ""
echo "  3. Start services:"
echo "       systemctl start sentinelflux caddy"
echo ""
echo "  4. Check status:"
echo "       systemctl status sentinelflux caddy"
echo "       journalctl -u sentinelflux -f"
echo ""
echo "  5. Point a remote runner at this dashboard (from your local machine):"
echo "       sentinelflux runner --server https://app.sentinelflux.in --token <token-from-dashboard>"
