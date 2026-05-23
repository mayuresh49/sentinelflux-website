#!/usr/bin/env bash
# Bootstrap a fresh GCP e2-micro VM (Ubuntu 24.04) for SentinelFlux dashboard.
# Run as root: bash scripts/gcp-setup.sh
#
# What this does vs server-setup.sh:
#   - Adds 512 MB swap (e2-micro has only 1 GB RAM)
#   - Skips Playwright install (runs server-side; use remote runner for Playwright-based tests)
#   - Sets --workers 1 for uvicorn (already in sentinelflux.service)
#   - Caddy auto-provisions TLS for app.sentinelflux.in via Let's Encrypt
set -euo pipefail

REPO="git@github.com:mayuresh49/sentinelflux-app.git"
APP_USER="sentinelflux"
APP_DIR="/home/${APP_USER}/app"
PYTHON="python3.12"
DEPLOY_KEY="/home/${APP_USER}/.ssh/sentinelflux_deploy"

echo "==> Installing system packages"
apt-get update -qq
apt-get install -y git "${PYTHON}" "${PYTHON}-venv" python3-pip ufw curl \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2  # WeasyPrint PDF deps

echo "==> Adding 512 MB swap (safety net for WeasyPrint PDF spikes)"
if [ ! -f /swapfile ]; then
    fallocate -l 512M /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Installing Caddy"
curl -fsSL https://caddyserver.com/install.sh | bash

echo "==> Configuring firewall"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> Creating app user"
id -u "${APP_USER}" &>/dev/null || useradd -m -s /bin/bash "${APP_USER}"

echo "==> Configuring SSH deploy key for private repo"
DEPLOY_KEY_DIR="/home/${APP_USER}/.ssh"
mkdir -p "${DEPLOY_KEY_DIR}"
chmod 700 "${DEPLOY_KEY_DIR}"
chown "${APP_USER}:${APP_USER}" "${DEPLOY_KEY_DIR}"

if [ ! -f "${DEPLOY_KEY}" ]; then
    echo ""
    echo "  Deploy key not found at ${DEPLOY_KEY}."
    echo "  Run these steps BEFORE re-running this script:"
    echo ""
    echo "  1. On your LOCAL machine, generate a key:"
    echo "       ssh-keygen -t ed25519 -f ~/.ssh/sentinelflux_deploy -N ''"
    echo ""
    echo "  2. Add the PUBLIC key to your private GitHub repo:"
    echo "       GitHub → sentinelflux-app → Settings → Deploy Keys → Add deploy key"
    echo "       Paste contents of: ~/.ssh/sentinelflux_deploy.pub"
    echo "       Title: gcp-vm  |  Allow write access: NO"
    echo ""
    echo "  3. Copy the PRIVATE key to this VM:"
    echo "       scp ~/.ssh/sentinelflux_deploy root@<VM-IP>:${DEPLOY_KEY}"
    echo "       chmod 600 ${DEPLOY_KEY}"
    echo "       chown ${APP_USER}:${APP_USER} ${DEPLOY_KEY}"
    echo ""
    echo "Then re-run this script."
    exit 1
fi
chmod 600 "${DEPLOY_KEY}"
chown "${APP_USER}:${APP_USER}" "${DEPLOY_KEY}"

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
    chown "${APP_USER}:${APP_USER}" "${SSH_CONFIG}"
    chmod 600 "${SSH_CONFIG}"
fi

echo "==> Cloning private repo"
if [ ! -d "${APP_DIR}" ]; then
    sudo -u "${APP_USER}" git clone "${REPO}" "${APP_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
fi

echo "==> Creating virtualenv and installing dependencies"
sudo -u "${APP_USER}" bash -c "
    cd ${APP_DIR}
    ${PYTHON} -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet -e '.[all]'
"

# NOTE: Playwright is intentionally NOT installed on this VM.
# A11y scans, visual regression, and AppExplorer run via the remote runner
# daemon on your local machine (sentinelflux runner --server https://app.sentinelflux.in).

echo "==> Installing systemd service"
cp "${APP_DIR}/scripts/sentinelflux.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable sentinelflux

echo "==> Configuring Caddy (app.sentinelflux.in → localhost:8765)"
cp "${APP_DIR}/scripts/Caddyfile.prod" /etc/caddy/Caddyfile
systemctl enable caddy

echo ""
echo "Setup complete. Before starting services:"
echo ""
echo "  1. Add DNS A record in GoDaddy: app → $(curl -s ifconfig.me 2>/dev/null || echo '<this VM external IP>')"
echo ""
echo "  2. Copy and fill in the env file:"
echo "       cp ${APP_DIR}/.env.example ${APP_DIR}/.env"
echo "       nano ${APP_DIR}/.env"
echo "       # Required: SECRET_KEY, MISTRAL_API_KEY (or ANTHROPIC_API_KEY)"
echo "       # Leave OLLAMA_BASE_URL empty — no local Ollama on this VM"
echo ""
echo "  3. Seed the first admin user:"
echo "       sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python ${APP_DIR}/scripts/seed_admin.py \\"
echo "           --email your@email.com --password yourpassword"
echo ""
echo "  4. Start services:"
echo "       systemctl start sentinelflux caddy"
echo ""
echo "  5. Check status:"
echo "       systemctl status sentinelflux caddy"
echo "       journalctl -u sentinelflux -f"
echo ""
echo "  6. Point a remote runner at this dashboard (from your local machine):"
echo "       sentinelflux runner --server https://app.sentinelflux.in --token <token-from-dashboard>"
echo "       # Generate token: Config → Runner Tokens in the dashboard"
