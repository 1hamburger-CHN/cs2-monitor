# CS2 Monitor

CS2 饰品价格监控系统 — Web 管理后台 + 定时爬虫 + Server酱 个人微信推送。

## 快速开始

### 1. 环境准备
- Python 3.11+
- MySQL 8.0+
- 创建数据库: `CREATE DATABASE cs2monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`

### 2. 配置
```
cp .env.example .env
cp config.yaml.example config.yaml
# 编辑 .env — 填入 MySQL 连接信息和 ENCRYPTION_KEY
```

### 3. 初始化
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/build_item_map.py
alembic upgrade head
python scripts/manage_invites.py create 1 365
```

### 4. 启动 Web 服务
```
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. 启动调度器（另一个终端）
```
python -m scheduler.main
```

### 6. 部署到服务器
```
sudo cp deploy/systemd/cs2-monitor-web.service /etc/systemd/system/
sudo cp deploy/systemd/cs2-monitor-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cs2-monitor-web cs2-monitor-scheduler
```

### 7. 配置 Caddy
```
sudo cp deploy/caddy/Caddyfile /etc/caddy/
sudo systemctl reload caddy
```
