# CS2 饰品价格监控系统 — 设计文档

> 最后更新：2026-06-08（整合全部讨论决策）

## 概述

24 小时运行在腾讯云服务器上的 CS2 饰品价格监控系统。用户通过 Web 管理后台配置监控列表和预警价格，系统定时爬取多平台价格，触发条件时通过 Server酱 推送到用户个人微信。支持多用户，每个用户独立接收自己的告警。

## 数据源

| 平台 | 说明 |
|------|------|
| CSQAQ | 国内饰品价格（聚合 BUFF / C5Game / 悠悠有品） |
| SteamDT | 国内饰品价格（聚合 BUFF / C5Game / 悠悠有品） |
| Steam Inventory API | 读取用户公开库存 (`steamcommunity.com/inventory/{steam_id}/730/2`) |

> 用户注册时必须选择 CSQAQ 或 SteamDT 作为价格数据源（二选一）。DMarket 已移除。

## 交互模型

```
┌─────────────────────────────┐     ┌──────────────────────────┐
│      Web 管理后台            │     │  Server酱（仅推送）          │
│                             │     │                          │
│  · 用户注册登录（邀请码）    │     │  · 价格告警推送           │
│  · 选择数据源（CSQAQ/SteamDT)│     │  · 每日持仓日报           │
│  · 配置监控列表 & 预警价     │     │  · 推送到个人微信          │
│  · 查看持仓 & 价格走势       │     │                          │
│  · 告警历史                  │     │                          │
└─────────────────────────────┘     └──────────────────────────┘
```

## 架构

```
┌──────────────────────────────────────────────────┐
│              FastAPI Web Server                   │
│                                                  │
│  ┌──────────┐ ┌───────────┐ ┌───────────────┐   │
│  │ 用户模块  │ │ 监控管理   │ │ 价格/走势查看  │   │
│  │ 邀请码注册│ │ 饰品 CRUD  │ │ 历史快照查询   │   │
│  │ Session   │ │ 预警价设置 │ │ 告警记录       │   │
│  └──────────┘ └───────────┘ └───────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │         APScheduler 后台任务              │    │
│  │                                          │    │
│  │   crawlers/          storage.py          │    │
│  │   ├── csqaq.py       MySQL 读写            │    │
│  │   ├── steamdt.py                         │    │
│  │   └── steam_inventory.py                 │    │
│  │                   │                      │    │
│  │                   ▼                      │    │
│  │              alerter.py                  │    │
│  │         规则引擎 → Server酱推送             │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## 数据流

```
Web 后台 → 用户配置监控列表 → 写入 MySQL
                         ↓
定时器触发 → 爬虫拉价格 → 写入 MySQL（价格快照表）
                       → alerter 对比规则 → 命中 → Server酱推个人微信
库存刷新(低频 6h) → 写入库存表 → 自动加入监控列表
每日定时 → 聚合查询 → 持仓日报 → Server酱推送
```

## 数据库表 (MySQL)

- **users** — 用户（username, password_hash, steam_id, steam_api_key_encrypted, server_chan_key, data_source, created_at）
- **invite_codes** — 邀请码（code, created_by, max_uses=1, used_count=0, is_active=true, created_at, expires_at）
- **price_snapshots** — 价格快照（market_hash_name, platform, price, timestamp）
- **inventory** — 用户库存（user_id, asset_id, market_hash_name, image_url, tradable）
- **watchlist** — 监控列表（user_id, market_hash_name, target_price, cost_price, qty, mode, enabled）
- **alert_log** — 告警记录（user_id, market_hash_name, rule_type, old_price, new_price, sent_at）

> 多用户场景：inventory / watchlist / alert_log 均通过 user_id 关联用户。同一饰品被多用户监控时，爬虫只拉一次价格，按用户各自规则判定推送。用户之间数据不互通。

## 饰品名称标准化（方案 B + 辅助映射表）

- 统一标识：Steam `market_hash_name`，如 `"AK-47 | Redline (Field-Tested)"`
- 数据来源：ByMykel/CSGO-API 开源项目，提供所有 CS2 饰品的结构化 JSON
- 映射表自动生成：从 API 数据拼出 market_hash_name 及中英文别名
- 用户输入中文名或英文名 → 查映射表 → 找到标准 market_hash_name → 各爬虫以此匹配
- 映射表打包在项目内，启动时加载

## 三种监控模式

### 模式一：单品盯价
- 用户设定目标饰品 + 心理价位
- `current_price <= target_price` → 推送

### 模式二：持仓组合
- 维护持仓列表（饰品名 + 买入价 + 数量）
- 计算总值和涨跌幅
- `abs(current_price - cost_price) / cost_price >= threshold%` → 推送

### 模式三：市场扫描
- 批量扫饰品，算涨跌排行
- 输出 Top N 涨/跌

## 库存联动

1. 用户在 Web 后台配置 Steam ID + API Key → 首次拉取库存 → 写入 inventory 表
2. 库存中价值 > 阈值的饰品可一键加入监控列表（默认 ¥10，可配置）
3. 库存刷新频率低于价格刷新（建议 6 小时一次）
4. 库存为私密时需要用户将库存设为公开，或提供 Steam Web API Key

## 通知

**Server酱** — 通过 Webhook 推送到用户个人微信：

- **实时告警**：价格触发条件时立即推送
- **每日日报**：持仓总市值 + 当日涨跌 + 触发的告警数

用户注册时填入自己的 Server酱 SendKey，每个用户独立配置。

接入方式：POST JSON 到 `https://sctapi.ftqq.com/{send_key}.send`

推送格式示例：
```
[CS2 价格告警]
AK-47 | 红线 (久经沙场)
当前: ¥85.50 | 目标: ¥80.00 | 跌幅: -2.3%
平台: CSQAQ
```

日报格式示例：
```
[CS2 持仓日报 - 6月8日]
持仓总值: ¥12,350 (+2.3%)
AK-47 | 红线: ¥85.50 (+0.5%)
AWP | 二西莫夫: ¥320.00 (-1.2%)
今日告警: 2 次
```

## 反爬策略

- 硬编码 5 分钟间隔，足够 100 件饰品规模
- 遇到 429 自动指数退避
- 各爬虫独立间隔，互不影响
- Steam Inventory API 走官方接口，遵守 rate limit

## 数据保留

- 30 天内：保留每条价格快照
- 30 天以上：保留每小时聚合（avg_price, min_price, max_price, sample_count）
- 每天凌晨 2:00 定时任务自动清理聚合

## 安全方案

| 安全项 | 方案 |
|--------|------|
| HTTPS | Caddy 反向代理 + Let's Encrypt |
| Steam API Key 存储 | Fernet 对称加密，密钥存环境变量 |
| 用户密码 | bcrypt/passlib 哈希 |
| XSS | Jinja2 模板自动转义 |
| SQL 注入 | SQLAlchemy ORM 参数化查询 |
| CSRF | FastAPI CSRF 中间件 |
| 访问控制 | 邀请码注册，登录后才能访问 |
| 服务器 | SSH Key 登录，禁密码，仅开放 80/443 |

> Steam API Key 密钥权限有限（仅查询公开库存，不能交易/改设置），即使泄露影响可控。

## 用户身份认证

- 管理员生成邀请码，分发给受信任的朋友
- 注册时填入邀请码 + 用户名 + 密码
- 邀请码可设置使用次数上限
- 登录后 Session 管理，FastAPI Session 中间件

## 部署

- 腾讯云轻量服务器（2 GB 内存）
- Python 3.x + FastAPI + Uvicorn
- Caddy 反向代理 + HTTPS
- Docker 部署（可选，V1 可直接 systemd）
- 无 LLM 依赖：纯 HTTP 请求 + MySQL + Webhook

## 技术选型

| 层面 | 选型 |
|------|------|
| Web 框架 | FastAPI |
| 模板引擎 | Jinja2 |
| ORM | SQLAlchemy |
| 定时任务 | APScheduler |
| 数据库 | MySQL |
| 反向代理 | Caddy |
| 加密 | cryptography (Fernet) |
| 密码哈希 | passlib (bcrypt) |
| 通知 | Server酱 (Webhook → 个人微信) |

## 决策记录

| # | 议题 | 决策 | 理由 |
|---|------|------|------|
| Q1 | 反爬策略 | 硬编码 5min + 429 退避 | 100 件饰品、2 平台规模小 |
| Q2 | 名称标准化 | 方案 B + 辅助映射表 | market_hash_name 唯一标识，ByMykel API 自动生成映射 |
| Q3 | 日/周报告 | 极简日报 | 心跳检测 + 极低开发成本 |
| Q4 | 数据保留 | 30 天全量 + 老数据小时聚合 | 平衡存储和查询精度 |
| Q5 | Web 看板 | V1 必做 | Web 管理后台是用户交互主入口 |
| Q6 | 用户界面 | Web 管理 + Server酱推送 | Web 负责配置管理，Server酱推个人微信 |
| — | DMarket | 移除 | 聚焦国内平台 |
| — | 通知方式 | Server酱 | 推个人微信、免费、国内直连 |
| — | 用户认证 | 邀请码注册 | 5-10 人小圈子，简单可控 |
| — | 安全 | 见安全方案 | 最低可行安全，覆盖主要攻击面 |
| — | 数据库 | MySQL | 用户已有，支持并发写入 |

## 后续迭代（V2+）

- 直接爬取源站（BUFF / C5Game / 悠悠有品）
- 价格走势图（charts.js 或其他前端库）
- 多档在售价、成交量等深度数据
- 全功能周报/月报
- 个人微信消息指令交互
- 多数据源切换

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 6 issues, 0 critical gaps |

**VERDICT: ENG REVIEW CLEARED — ready to implement.**

### 审查决策

| # | 类别 | 问题 | 决策 |
|---|------|------|------|
| A1 | Architecture | APScheduler 多 Worker 重复执行 | 独立调度进程（systemd service），与 Web Server 分离 |
| A2 | Architecture | Server酱 SendKey 未加密 | Fernet 加密存储，与 Steam API Key 同方案 |
| A3 | Architecture | 爬虫超时/失败处理 | 首选数据源挂了自动 fallback 备选源，双源都挂则排队重试 |
| A4 | Architecture | 数据库迁移策略 | Alembic（SQLAlchemy 官配） |
| C1 | Code Quality | 爬虫基类抽象 | 独立实现每个爬虫，实施中自然浮现共性后提取 |
| P1 | Performance | 爬虫并发策略 | asyncio.Semaphore(5) 小批量并行 |

### 设计文档变更项

以下内容需在实施前补充到设计文档：
- [ ] 数据源模型更新：用户选择"首选"数据源，支持自动 fallback
- [ ] 独立调度进程架构说明
- [ ] SendKey 加密方案
- [ ] Alembic 迁移配置
- [ ] 爬虫容错流程（fallback + 重试队列）
- [ ] `watchlist.mode` 字段值定义（mode_1 / mode_2 / mode_3）
- [ ] 测试策略章节（分层渐进：alerter → auth → crawler）
- [ ] ByMykel 映射表刷新策略（建议每周拉取最新版本）

### 测试覆盖缺口

24 个测试路径待覆盖（绿色项目）。分层顺序：
1. Layer 1: alerter.py + notifier.py 单元测试（纯逻辑）
2. Layer 2: auth.py + watchlist.py API 集成测试
3. Layer 3: crawler mock 测试 + E2E fallback 测试

### NOT in Scope (V1)

- WebSocket 实时价格推送
- 价格走势图（charts.js）
- 企微机器人通道
- 多数据源同显对比
- OpenID 登录 / OAuth
- Docker 部署（systemd 够用）

### What Already Exists

无。绿色项目，从零构建。
