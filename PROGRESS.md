# CS2 饰品监控 — 开发进度

> 最后更新：2026-06-09 (下午) | 18 commits | 90+ files

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

### 前端 (Vue 3 + Vite + PWA) 🆕
- Vite + Vue 3 + TypeScript 项目 (`frontend/`)
- Vue Router 4（7 路由 + 导航守卫）+ Pinia 状态管理
- 7 页面 + 9 组件 + anime.js 动效
- PWA：manifest.json + Service Worker（离线缓存 + Web Push）
- 暗色主题（Fira Code + CSS 变量，来自 design/pwa-v2.html）
- **构建通过** ✅ TypeScript 零错误，产物在 `app/static/spa/`

### 后端 API 🆕
- 18 个 JSON 端点 (`/api/v1/*`) — 认证/仪表盘/CRUD/搜索/告警/设置/WebPush

### 设计
- `design/pwa-v2.html` — PWA 设计稿（Fira Code + 暗色仪表盘）

## 待做

1. ~~**前端重写**~~ ✅
2. **FastAPI SPA**：SPA 占据 `/`，移除 Jinja2 路由
3. **PWA 图标**：192x192 + 512x512 PNG
4. **Web Push 后端**：VAPID + pywebpush
5. **集成测试修复**
6. **CSQAQ 缓存预填充**
7. **上线部署**：腾讯云 + Caddy

## 设计决策

| 议题 | 决策 |
|------|------|
| 数据源 | CSQAQ 官方 API |
| 通知 | 自建 PWA Web Push（不用第三方） |
| 数据库 | MySQL |
| 图片 | CSQAQ CDN |
| 前端 | Vue 3 PWA + anime.js ✅ |
| 动画 | anime.js（价格跳动、列表入场、告警脉冲） |

## 启动

```bash
# 后端
cd d:\饰品监控
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端开发（热更新，API 代理到 8000）
cd d:\饰品监控\frontend && npm run dev

# 前端生产构建 → app/static/spa/
cd d:\饰品监控\frontend && npm run build

# 调度器
PYTHONPATH=. CSQAQ_API_TOKEN=<token> python -m scheduler.main
```
