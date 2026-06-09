#!/bin/bash
# CS2 Monitor — One-command deployment script
# Usage: sudo bash deploy.sh
set -euo pipefail

APP_DIR="/opt/cs2-monitor"
VENV_DIR="$APP_DIR/venv"
DOMAIN="${DOMAIN:-cs2monitor.example.com}"

echo "=== CS2 Monitor Deployment ==="
echo "Domain: $DOMAIN"

if [ ! -f "app/main.py" ]; then
    echo "ERROR: Run from project root."; exit 1
fi

echo "[1/7] Installing packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3.11 python3.11-venv mysql-server caddy

if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y -qq nodejs
fi

echo "[2/7] Creating user..."
id cs2monitor &>/dev/null || sudo useradd -r -s /bin/false -d "$APP_DIR" cs2monitor

echo "[3/7] Copying files..."
sudo mkdir -p "$APP_DIR"
sudo cp -r app scheduler frontend scripts migrations data deploy requirements.txt alembic.ini config.yaml.example .env.example "$APP_DIR/"
sudo chown -R cs2monitor:cs2monitor "$APP_DIR"

echo "[4/7] Configuring..."
if [ ! -f "$APP_DIR/.env" ]; then
    sudo cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "  Created .env — EDIT: sudo nano $APP_DIR/.env"
    read -p "  Press Enter after editing..." _
fi

echo "[5/7] Python venv..."
sudo -u cs2monitor python3.11 -m venv "$VENV_DIR"
sudo -u cs2monitor "$VENV_DIR/bin/pip" install -q --upgrade pip
sudo -u cs2monitor "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[6/7] Building frontend..."
cd "$APP_DIR/frontend"
sudo -u cs2monitor npm install
sudo -u cs2monitor npm run build
cd "$APP_DIR"

if [ ! -f "$APP_DIR/app/static/spa/index.html" ]; then
    echo "ERROR: Frontend build failed!"; exit 1
fi

echo "[7/7] Services..."
sudo sed -i "s/cs2monitor.example.com/$DOMAIN/" "$APP_DIR/deploy/caddy/Caddyfile"
sudo cp "$APP_DIR/deploy/systemd/"*.service /etc/systemd/system/
sudo cp "$APP_DIR/deploy/caddy/Caddyfile" /etc/caddy/Caddyfile
sudo systemctl daemon-reload
sudo systemctl enable --now cs2-monitor-web cs2-monitor-scheduler
sudo systemctl reload caddy

echo ""
echo "=== Done! ==="
echo "Access: https://$DOMAIN"
echo "Status: sudo systemctl status cs2-monitor-web cs2-monitor-scheduler"
echo "Logs:   sudo journalctl -u cs2-monitor-web -f"
