# CS2 饰品监控 — 开发进度

> 最后更新：2026-06-09 | 16 commits | 60+ files

## 已完成

### 后端 (FastAPI + MySQL)
- 配置管理、数据库引擎、加密工具
- 6 张表：users, invite_codes, watchlist_items, price_snapshots, inventory_items, alert_logs
- 用户认证（邀请码注册 + bcrypt 登录 + Session）
- 仪表盘、监控 CRUD、用户设置
- 饰品映射：13763 件 + 中文搜索（红线→Redline）
- Alembic 数据库迁移

### 调度器 (独立进程)
- CSQAQ 官方 API 爬虫（429 重试 + ID 缓存 + 饰品图片）
- 告警引擎（三种模式：盯价/持仓/扫描）
- Server酱 通知 webhook

### 测试
- alerter: 8/8 ✅ | notifier: 3/3 ✅ | item_mapper: 7/7 ✅
- auth/watchlist 集成测试待修复（需测试数据库）

### 设计
- `design/pwa-v2.html` — PWA 设计稿（Fira Code + 暗色仪表盘 + 真实图片）

## 待做

1. **前端重写**：Vue 3 + Vite + PWA + anime.js (Web Push 通知 + 动画)
2. **FastAPI 改纯 API**：删除 Jinja2 模板
3. **集成测试修复**
4. **CSQAQ 首次缓存预填充**（减少限速等待）
5. **上线部署**：腾讯云 + Caddy HTTPS

## 设计决策

| 议题 | 决策 |
|------|------|
| 数据源 | CSQAQ 官方 API |
| 通知 | 自建 PWA Web Push（不用第三方） |
| 数据库 | MySQL |
| 图片 | CSQAQ CDN |
| 前端 | Vue 3 PWA + anime.js（替代 Jinja2） |
| 动画 | anime.js（价格跳动、列表入场、告警脉冲） |

## 启动

```
cd d:\饰品监控
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
PYTHONPATH=. CSQAQ_API_TOKEN=<token> python -m scheduler.main
```
