# CS2 饰品监控 · 状态

> 2026-06-10 · live at https://skinmonitor.cloud

## 运行中

| 服务 | 状态 |
|------|------|
| Web (FastAPI) | ✅ `cs2monitor-web` |
| Scheduler (价格 + 告警) | ✅ 每 5 分钟 (asyncio loop) |
| MySQL | ✅ `cs2monitor-mysql` |
| Caddy (HTTPS) | ✅ 禁用 H3 (腾讯云防火墙) |

## 功能

- 用户认证 (邀请码 + bcrypt + Session)
- 仪表盘、监控列表、添加饰品、告警中心、用户设置
- CSQAQ API 爬虫 (25,348 条中文搜索映射)
- 告警引擎 (盯价/持仓/扫描)
- Web Push 后端 (VAPID + pywebpush)
- **anime.js 动效** ✅ — 数字跳动、列表入场、价格闪色、告警脉冲

## 测试

| 模块 | 结果 |
|------|------|
| alerter | 8/8 ✅ |
| notifier | 3/3 ✅ |
| item_mapper | 7/7 ✅ |
| auth API | 7/7 ✅ |

## 待做

1. **PWA 图标** — 192×192 + 512×512 PNG
2. **iOS Web Push 验证** — 需实际设备测试
3. **Android 原生** — Capacitor + UniPush 厂商推送
4. **Docker 镜像重建** — 正式 `docker build` 消除 `docker cp` 补丁
5. **CSQAQ 缓存预填充** — 减少首次查询延迟

## 部署

```bash
# 构建前端
cd frontend && npm run build

# 推送到服务器
git push origin master

# 或手动
ssh root@82.156.84.213
cd /opt/cs2-monitor && docker compose up -d --build
```
