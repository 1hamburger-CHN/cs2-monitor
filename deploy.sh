#!/bin/bash
# CS2 Monitor — One-command deployment script
# Target: Ubuntu 22.04+ / Debian 12+
set -euo pipefail

APP_DIR="/opt/cs2-monitor"
VENV_DIR="$APP_DIR/venv"
PYTHON="${PYTHON:-python3.11}"

echo "=== CS2 Monitor Deployment ==="

# 1. System dependencies
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3.11 python3.11-venv mysql-server caddy

# 2. Create user
echo "[2/6] Creating cs2monitor user..."
if ! id cs2monitor &>/dev/null; then
    sudo useradd -r -s /bin/false -d "$APP_DIR" cs2monitor
fi

# 3. Setup application directory
echo "[3/6] Setting up $APP_DIR..."
sudo mkdir -p "$APP_DIR"
sudo cp -r . "$APP_DIR/"
sudo chown -R cs2monitor:cs2monitor "$APP_DIR"

# 4. Python virtual environment
echo "[4/6] Setting up Python venv..."
sudo -u cs2monitor python3.11 -m venv "$VENV_DIR"
sudo -u cs2monitor "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# 5. Build frontend (if Node.js available)
echo "[5/6] Building frontend..."
if command -v node &>/dev/null; then
    cd "$APP_DIR/frontend"
    npm install --production
    npm run build
    cd "$APP_DIR"
else
    echo "  Node.js not found — skipping frontend build"
    echo "  Install Node.js 18+ and run: cd $APP_DIR/frontend && npm install && npm run build"
fi

# 6. Setup MySQL database
echo "[6/6] Setting up database..."
if sudo mysql -e "SELECT 1" &>/dev/null; then
    sudo mysql <<SQL
CREATE DATABASE IF NOT EXISTS cs2monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'cs2monitor'@'localhost' IDENTIFIED BY 'change-me-password';
GRANT ALL PRIVILEGES ON cs2monitor.* TO 'cs2monitor'@'localhost';
FLUSH PRIVILEGES;
SQL
    echo "  Database created. Change password in .env!"
else
    echo "  MySQL not accessible — create database manually"
fi

# 7. Install systemd services
echo ""
echo "=== Installing systemd services ==="
sudo cp "$APP_DIR/deploy/systemd/cs2-monitor-web.service" /etc/systemd/system/
sudo cp "$APP_DIR/deploy/systemd/cs2-monitor-scheduler.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cs2-monitor-web cs2-monitor-scheduler

# 8. Setup Caddy
echo ""
echo "=== Setting up Caddy ==="
sudo cp "$APP_DIR/deploy/caddy/Caddyfile" /etc/caddy/Caddyfile
sudo systemctl reload caddy

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "Next steps:"
echo "1. Edit $APP_DIR/.env — set DATABASE_URL, ENCRYPTION_KEY, SECRET_KEY, CSQAQ_API_TOKEN"
echo "2. Build item map: cd $APP_DIR && $VENV_DIR/bin/python scripts/build_item_map.py"
echo "3. Run migrations: cd $APP_DIR && $VENV_DIR/bin/python -m alembic upgrade head"
echo "4. Create invite code: cd $APP_DIR && $VENV_DIR/bin/python scripts/manage_invites.py create 1 365"
echo "5. Check status: sudo systemctl status cs2-monitor-web cs2-monitor-scheduler caddy"
echo "6. Access: https://cs2monitor.example.com"
