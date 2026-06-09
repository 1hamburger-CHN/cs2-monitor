# CS2 Monitor

CS2 饰品价格监控系统 — Vue 3 PWA 前端 + FastAPI 后端 + 定时爬虫 + 推送通知。

## 架构

```
浏览器 (Vue 3 PWA) ---> Caddy :443 ---> FastAPI :8000 ---> MySQL
                                              |-- /api/v1/*  (JSON API)
                                              |-- /*  (SPA index.html)
调度器 (独立进程) ---> CSQAQ API ---> MySQL + ServerChan + Web Push
```

## 本地开发

```bash
# 1. 后端
cp .env.example .env && cp config.yaml.example config.yaml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_item_map.py
alembic upgrade head
python scripts/manage_invites.py create 1 365

# 2. 前端
cd frontend && npm install && npm run build && cd ..

# 3. 启动
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000
PYTHONPATH=. CSQAQ_API_TOKEN=xxx python -m scheduler.main  # 另一个终端
```

访问 http://127.0.0.1:8000 进入 SPA 仪表盘。

## 一键部署 (Ubuntu/Debian)

```bash
cd /opt/cs2-monitor && sudo bash deploy.sh
```

脚本自动完成: 系统依赖, Python venv, 前端构建, MySQL 初始化, systemd, Caddy。

## 手动部署

```bash
sudo apt install python3.11 python3.11-venv mysql-server caddy
sudo useradd -r -s /bin/false -d /opt/cs2-monitor cs2monitor
sudo cp -r . /opt/cs2-monitor/ && sudo chown -R cs2monitor:cs2monitor /opt/cs2-monitor
cd /opt/cs2-monitor
sudo -u cs2monitor python3.11 -m venv venv
sudo -u cs2monitor venv/bin/pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
sudo -u cs2monitor venv/bin/python scripts/build_item_map.py
sudo -u cs2monitor venv/bin/python -m alembic upgrade head
sudo -u cs2monitor venv/bin/python scripts/manage_invites.py create 1 365
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cs2-monitor-web cs2-monitor-scheduler
sudo cp deploy/caddy/Caddyfile /etc/caddy/
sudo systemctl reload caddy
```

## 项目结构

```
app/           FastAPI (main.py, routes/api.py, models/)
scheduler/     独立调度进程 (爬虫 + 告警 + 推送)
frontend/      Vue 3 PWA (7 页面 + 9 组件 + anime.js)
deploy/        Caddy + systemd 部署配置
scripts/       CLI 工具 (邀请码/饰品映射)
migrations/    Alembic 数据库迁移
tests/         pytest 测试
```

## API 端点 (/api/v1/)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /me | 当前用户 |
| POST | /auth/login | 登录 |
| POST | /auth/register | 注册 |
| GET | /dashboard | 仪表盘 |
| GET/POST | /watchlist | 监控 CRUD |
| PATCH/DELETE | /watchlist/:id | 更新/删除 |
| GET | /items/search?q= | 饰品搜索 |
| GET | /alerts | 告警历史 |
| GET/PUT | /settings | 用户设置 |
| POST | /push/subscribe | Web Push 订阅 |

## 环境变量

| 变量 | 说明 |
|------|------|
| DATABASE_URL | MySQL 连接串 |
| ENCRYPTION_KEY | Fernet 加密密钥 |
| SECRET_KEY | Session 密钥 |
| CSQAQ_API_TOKEN | CSQAQ API Token |
| VAPID_PUBLIC_KEY | Web Push 公钥 |
| VAPID_PRIVATE_KEY | Web Push 私钥 |
