# CS2 饰品价格监控系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 CS2 饰品价格监控 Web 应用 — 用户注册登录、配置监控列表、系统定时爬取 CSQAQ/SteamDT 价格、触发条件时通过 Server酱 推送到个人微信。

**Architecture:** FastAPI Web Server（用户交互） + 独立 APScheduler 进程（后台爬虫/告警） + MySQL 数据库。Web 和 Scheduler 通过共享数据库通信，各自独立部署（systemd 两个 service）。爬虫支持首选数据源故障时自动 fallback 备选源。

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, SQLAlchemy 2.0 (async), MySQL, APScheduler 4.x, Alembic, cryptography (Fernet), passlib (bcrypt), httpx (async HTTP), Caddy (反向代理)

---

## 文件结构

```
cs2-monitor/
├── app/                          # Web 应用
│   ├── __init__.py
│   ├── main.py                   # FastAPI 入口 + lifespan
│   ├── config.py                 # 配置管理（环境变量 + YAML）
│   ├── database.py               # SQLAlchemy async engine + session
│   ├── encryption.py             # Fernet 加解密工具
│   ├── item_mapper.py            # ByMykel 数据 → market_hash_name 映射表
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # User ORM model
│   │   ├── invite_code.py        # InviteCode ORM model
│   │   ├── price_snapshot.py     # PriceSnapshot ORM model
│   │   ├── inventory_item.py     # InventoryItem ORM model
│   │   ├── watchlist_item.py     # WatchlistItem ORM model
│   │   └── alert_log.py          # AlertLog ORM model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── deps.py               # 依赖注入（login_required 等）
│   │   ├── auth.py               # 登录/注册/登出
│   │   ├── dashboard.py          # 首页仪表盘
│   │   ├── watchlist.py          # 监控列表 CRUD
│   │   ├── inventory.py          # 库存查看
│   │   └── alerts.py             # 告警历史
│   ├── templates/
│   │   ├── base.html.j2          # 基础布局
│   │   ├── login.html.j2         # 登录页
│   │   ├── register.html.j2      # 注册页
│   │   ├── dashboard.html.j2     # 仪表盘
│   │   ├── watchlist.html.j2     # 监控列表管理
│   │   ├── inventory.html.j2     # 库存页
│   │   └── alerts.html.j2        # 告警历史页
│   └── static/
│       └── style.css
├── scheduler/                    # 独立调度进程
│   ├── __init__.py
│   ├── main.py                   # 调度器入口
│   ├── tasks.py                  # 定时任务定义
│   ├── crawlers/
│   │   ├── __init__.py
│   │   ├── csqaq.py              # CSQAQ 爬虫
│   │   ├── steamdt.py            # SteamDT 爬虫
│   │   └── steam_inventory.py    # Steam 库存 API
│   ├── alerter.py                # 规则引擎（三种模式）
│   └── notifier.py               # Server酱 推送
├── scripts/
│   ├── build_item_map.py         # 从 ByMykel API 构建映射表
│   └── manage_invites.py         # 邀请码管理 CLI
├── migrations/                   # Alembic 迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── data/
│   └── item_aliases.json         # 饰品中英文映射表
├── deploy/
│   ├── caddy/Caddyfile
│   └── systemd/
│       ├── cs2-monitor-web.service
│       └── cs2-monitor-scheduler.service
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_watchlist.py
│   ├── test_alerter.py
│   ├── test_notifier.py
│   ├── test_item_mapper.py
│   └── test_crawlers.py
├── alembic.ini
├── requirements.txt
├── config.yaml.example
├── .env.example
└── README.md
```

---

## Phase 1: 项目骨架 + 配置 + 数据库

### Task 1: 项目初始化

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml.example`
- Create: `.env.example`
- Create: `app/__init__.py`, `scheduler/__init__.py`
- Create: `app/config.py`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
aiomysql==0.2.0
apscheduler==4.0.0
httpx==0.27.0
jinja2==3.1.4
passlib[bcrypt]==1.7.4
cryptography==43.0.0
python-multipart==0.0.9
pyyaml==6.0.2
alembic==1.13.0
pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 2: 创建 .env.example**

```
DATABASE_URL=mysql+aiomysql://cs2monitor:password@localhost:3306/cs2monitor
ENCRYPTION_KEY=change-me-generate-with-fernet
SECRET_KEY=change-me-random-string
ADMIN_PASSWORD=admin-change-me
```

- [ ] **Step 3: 创建 config.yaml.example**

```yaml
crawler:
  interval_seconds: 300
  request_timeout: 15
  max_concurrent: 5
  user_agent: "CS2-Monitor/1.0"
inventory:
  interval_hours: 6
  min_value_threshold: 10
retention:
  raw_days: 30
  cleanup_hour: 2
daily_report:
  hour: 20
notification:
  retry_count: 1
  retry_delay: 5
```

- [ ] **Step 4: 创建 app/config.py**

```python
"""应用配置管理。从环境变量和 YAML 文件加载配置。"""
import os
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://cs2monitor:password@localhost:3306/cs2monitor"
    encryption_key: str = ""
    secret_key: str = "dev-secret-change-in-production"
    admin_password_hash: str = ""
    crawler_interval_seconds: int = 300
    crawler_timeout: int = 15
    crawler_max_concurrent: int = 5
    crawler_user_agent: str = "CS2-Monitor/1.0"
    inventory_interval_hours: int = 6
    inventory_min_value: float = 10.0
    retention_raw_days: int = 30
    retention_cleanup_hour: int = 2
    daily_report_hour: int = 20
    notification_retry_count: int = 1
    notification_retry_delay: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @classmethod
    def from_yaml(cls, yaml_path: str = "config.yaml") -> "Settings":
        settings = cls()
        if Path(yaml_path).exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
            if yaml_config:
                if "crawler" in yaml_config:
                    for k, v in yaml_config["crawler"].items():
                        key = f"crawler_{k}"
                        if hasattr(settings, key):
                            setattr(settings, key, v)
                if "inventory" in yaml_config:
                    inv = yaml_config["inventory"]
                    if "min_value_threshold" in inv:
                        settings.inventory_min_value = inv["min_value_threshold"]
                    if "interval_hours" in inv:
                        settings.inventory_interval_hours = inv["interval_hours"]
                if "retention" in yaml_config:
                    r = yaml_config["retention"]
                    if "raw_days" in r:
                        settings.retention_raw_days = r["raw_days"]
                    if "cleanup_hour" in r:
                        settings.retention_cleanup_hour = r["cleanup_hour"]
                if "daily_report" in yaml_config:
                    settings.daily_report_hour = yaml_config["daily_report"].get("hour", 20)
                if "notification" in yaml_config:
                    n = yaml_config["notification"]
                    if "retry_count" in n:
                        settings.notification_retry_count = n["retry_count"]
                    if "retry_delay" in n:
                        settings.notification_retry_delay = n["retry_delay"]
        return settings


settings = Settings.from_yaml()
```

- [ ] **Step 5: 创建目录结构**

```bash
cd d:/饰品监控 && mkdir -p app/models app/routes app/templates app/static scheduler/crawlers scripts migrations/versions data tests deploy/caddy deploy/systemd
```

- [ ] **Step 6: git init + 首次提交**

```bash
cd d:/饰品监控 && git init && git add -A && git commit -m "feat: project scaffold — config, requirements, directory structure"
```

---

### Task 2: 数据库引擎 + 加密工具

**Files:**
- Create: `app/database.py`
- Create: `app/encryption.py`

- [ ] **Step 1: 创建 app/encryption.py**

```python
"""Fernet 对称加密。用于加密存储 Steam API Key 和 Server酱 SendKey。"""
from cryptography.fernet import Fernet
from app.config import settings


def get_fernet() -> Fernet:
    if not settings.encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY 未设置。生成方式: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(settings.encryption_key.encode())


def encrypt_value(value: str) -> str:
    if not value:
        return value
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    if not encrypted:
        return encrypted
    return get_fernet().decrypt(encrypted.encode()).decode()
```

- [ ] **Step 2: 创建 app/database.py**

```python
"""SQLAlchemy async engine + session 工厂。"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 3: Commit**

```bash
git add app/database.py app/encryption.py && git commit -m "feat: database engine + encryption utility"
```

---

### Task 3: 全部 ORM Models

**Files:**
- Create: `app/models/__init__.py`
- Create: `app/models/user.py`
- Create: `app/models/invite_code.py`
- Create: `app/models/watchlist_item.py`
- Create: `app/models/price_snapshot.py`
- Create: `app/models/inventory_item.py`
- Create: `app/models/alert_log.py`

- [ ] **Step 1: models/user.py**

```python
"""用户表。"""
import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    steam_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    steam_api_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    server_chan_key_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preferred_source: Mapped[str] = mapped_column(String(16), default="csqaq")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 2: models/invite_code.py**

```python
"""邀请码表。"""
import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(datetime.timezone.utc):
            return False
        if self.used_count >= self.max_uses:
            return False
        return True
```

- [ ] **Step 3: models/watchlist_item.py**

```python
"""用户监控列表表。"""
import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    market_hash_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    mode: Mapped[int] = mapped_column(Integer, default=1)
    threshold_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 4: models/price_snapshot.py**

```python
"""价格快照表 — 全局共用，无 user_id。"""
import datetime
from sqlalchemy import String, Float, Integer, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_hash_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(16), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("idx_snapshot_item_time", "market_hash_name", "timestamp"),
    )
```

- [ ] **Step 5: models/inventory_item.py**

```python
"""用户 Steam 库存表。"""
import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    market_hash_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tradable: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 6: models/alert_log.py**

```python
"""告警记录表。"""
import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    market_hash_name: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_type: Mapped[int] = mapped_column(Integer, nullable=False)
    old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_price: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    success: Mapped[bool] = mapped_column(Boolean, default=True)
```

- [ ] **Step 7: models/__init__.py**

```python
from app.models.user import User
from app.models.invite_code import InviteCode
from app.models.watchlist_item import WatchlistItem
from app.models.price_snapshot import PriceSnapshot
from app.models.inventory_item import InventoryItem
from app.models.alert_log import AlertLog

__all__ = ["User", "InviteCode", "WatchlistItem", "PriceSnapshot", "InventoryItem", "AlertLog"]
```

- [ ] **Step 8: Commit**

```bash
git add app/models/ && git commit -m "feat: all ORM models — 6 tables"
```

---

### Task 4: Alembic 迁移配置 + 首次迁移

- [ ] **Step 1: 初始化 Alembic**

```bash
cd d:/饰品监控 && alembic init migrations
```

- [ ] **Step 2: 修改 alembic.ini 中的 sqlalchemy.url**

```
sqlalchemy.url = mysql+aiomysql://cs2monitor:password@localhost:3306/cs2monitor
```

- [ ] **Step 3: 修改 migrations/env.py — 使用 async engine**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.database import Base
from app.models import *  # noqa: F401,F403

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 生成首次迁移**

```bash
cd d:/饰品监控
# 确保 MySQL 已创建数据库: CREATE DATABASE cs2monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

- [ ] **Step 5: Commit**

```bash
git add alembic.ini migrations/ && git commit -m "feat: alembic migration + initial schema"
```

---

## Phase 2: 认证系统

### Task 5: 用户注册 + 登录 + Session

**Files:**
- Create: `app/routes/__init__.py`, `app/routes/deps.py`, `app/routes/auth.py`
- Create: `app/main.py`
- Create: `tests/conftest.py`, `tests/test_auth.py`

- [ ] **Step 1: 编写测试 tests/test_auth.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_page_loads(client):
    response = await client.get("/register")
    assert response.status_code == 200
    assert "注册" in response.text


@pytest.mark.asyncio
async def test_login_page_loads(client):
    response = await client.get("/login")
    assert response.status_code == 200
    assert "登录" in response.text


@pytest.mark.asyncio
async def test_register_requires_valid_invite_code(client):
    response = await client.post("/register", data={
        "username": "testuser", "password": "testpass123", "invite_code": "INVALID"
    })
    assert response.status_code == 200
    assert "邀请码无效" in response.text


@pytest.mark.asyncio
async def test_login_with_wrong_password(client):
    response = await client.post("/login", data={
        "username": "nonexistent", "password": "wrong"
    })
    assert response.status_code == 200
    assert "用户名或密码错误" in response.text


@pytest.mark.asyncio
async def test_protected_page_redirects_when_not_logged_in(client):
    response = await client.get("/watchlist", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_auth.py -v
```
Expected: FAIL — `app.main` module not found.

- [ ] **Step 3: 创建 app/routes/deps.py**

```python
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def login_required(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=302)
    return user
```

- [ ] **Step 4: 创建 app/routes/auth.py**

```python
"""用户认证路由。"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from app.database import get_db
from app.models import User, InviteCode

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "register.html.j2", {"request": request}
    )


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # 校验邀请码
    result = await db.execute(
        select(InviteCode).where(InviteCode.code == invite_code.strip().upper())
    )
    code = result.scalar_one_or_none()
    if code is None or not code.is_valid:
        return request.app.state.templates.TemplateResponse(
            "register.html.j2",
            {"request": request, "error": "邀请码无效或已过期"},
        )
    # 检查用户名
    result = await db.execute(select(User).where(User.username == username.strip()))
    if result.scalar_one_or_none():
        return request.app.state.templates.TemplateResponse(
            "register.html.j2",
            {"request": request, "error": "用户名已被占用"},
        )
    # 创建用户
    user = User(username=username.strip(), password_hash=pwd_context.hash(password))
    db.add(user)
    code.used_count += 1
    await db.commit()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "login.html.j2", {"request": request}
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username.strip()))
    user = result.scalar_one_or_none()
    if user is None or not pwd_context.verify(password, user.password_hash):
        return request.app.state.templates.TemplateResponse(
            "login.html.j2",
            {"request": request, "error": "用户名或密码错误"},
        )
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
```

- [ ] **Step 5: 创建 app/main.py**

```python
"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.routes import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.templates = Jinja2Templates(directory="app/templates")
    yield


app = FastAPI(title="CS2 Monitor", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(auth.router, tags=["auth"])
```

- [ ] **Step 6: 创建最小模板测试通过**

创建 `app/templates/register.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}注册 - CS2 Monitor{% endblock %}
{% block content %}
<h1>注册</h1>
<form method="post">
    <input name="username" placeholder="用户名" required>
    <input name="password" type="password" placeholder="密码" required>
    <input name="invite_code" placeholder="邀请码" required>
    <button type="submit">注册</button>
</form>
{% endblock %}
```

创建 `app/templates/login.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}登录 - CS2 Monitor{% endblock %}
{% block content %}
<h1>登录</h1>
<form method="post">
    <input name="username" placeholder="用户名" required>
    <input name="password" type="password" placeholder="密码" required>
    <button type="submit">登录</button>
</form>
{% endblock %}
```

创建 `app/templates/base.html.j2`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CS2 Monitor{% endblock %}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <nav>{% if request.session.get("user_id") %}
        <a href="/dashboard">仪表盘</a>
        <a href="/watchlist">监控列表</a>
        <a href="/alerts">告警</a>
        <span style="float:right">{{ request.session.get("username") }} | <a href="/logout">登出</a></span>
    {% endif %}</nav>
    <main>{% if error %}<div class="alert alert-error">{{ error }}</div>{% endif %}
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

- [ ] **Step 7: Run tests**

```bash
python -m pytest tests/test_auth.py -v
```
Expected: PASS（需先创建数据库并运行 migration）

- [ ] **Step 8: Commit**

```bash
git add app/main.py app/routes/ app/templates/ tests/ && git commit -m "feat: auth system — register, login, logout, session middleware"
```

---

### Task 6: 邀请码管理 CLI

**Files:**
- Create: `scripts/manage_invites.py`

```python
#!/usr/bin/env python3
"""邀请码管理工具。"""
import secrets, sys, asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import InviteCode


def generate_code() -> str:
    return "CS2-" + secrets.token_hex(4).upper()


async def create_code(max_uses: int = 1, days_valid: int = 365):
    code_str = generate_code()
    expires = datetime.now(timezone.utc) + timedelta(days=days_valid)
    async with AsyncSessionLocal() as db:
        code = InviteCode(code=code_str, max_uses=max_uses, expires_at=expires)
        db.add(code)
        await db.commit()
        print(f"邀请码: {code_str}  (次数:{max_uses}  过期:{expires.strftime('%Y-%m-%d')})")


async def list_codes():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InviteCode).order_by(InviteCode.created_at.desc()))
        for c in result.scalars().all():
            status = "有效" if c.is_valid else "无效"
            print(f"{c.code:<20} {c.used_count}/{c.max_uses}  {status}")


async def deactivate_code(code_str: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InviteCode).where(InviteCode.code == code_str.strip().upper()))
        code = result.scalar_one_or_none()
        if code:
            code.is_active = False
            await db.commit()
            print(f"已停用: {code_str}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/manage_invites.py create|list|deactivate [args]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "create":
        uses = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        asyncio.run(create_code(uses, days))
    elif cmd == "list":
        asyncio.run(list_codes())
    elif cmd == "deactivate" and len(sys.argv) > 2:
        asyncio.run(deactivate_code(sys.argv[2]))
```

- [ ] **Commit**

```bash
git add scripts/ && git commit -m "feat: invite code management CLI"
```

---

## Phase 3: 饰品名称映射

### Task 7: ByMykel 映射表构建 + 查询

**Files:**
- Create: `scripts/build_item_map.py`
- Create: `app/item_mapper.py`
- Create: `tests/test_item_mapper.py`

- [ ] **Step 1: scripts/build_item_map.py**

```python
#!/usr/bin/env python3
"""从 ByMykel/CSGO-API 拉取饰品数据并生成本地映射表。"""
import json, httpx

API = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
WEAR_CN = {
    "Factory New": "崭新出厂", "Minimal Wear": "略有磨损",
    "Field-Tested": "久经沙场", "Well-Worn": "破损不堪", "Battle-Scarred": "战痕累累",
}


def build_name(name: str, wear: str, st: bool = False, souv: bool = False) -> str:
    prefix = "Souvenir " if souv else ("StatTrak™ " if st else "")
    return f"{prefix}{name} ({wear})"


def main():
    print("拉取 ByMykel/CSGO-API 皮肤数据...")
    resp = httpx.get(API, timeout=30)
    resp.raise_for_status()
    aliases = {}
    for skin in resp.json():
        name = skin["name"]
        for wear in skin.get("wears", []):
            wn = wear["name"]
            for st, souv in [(False, False), (True, False) if skin.get("stattrak") else (False, False)]:
                mn = build_name(name, wn, st, souv)
                aliases[mn] = {
                    "name": name, "weapon": skin.get("weapon", {}).get("name", ""),
                    "wear": wn, "wear_cn": WEAR_CN.get(wn, wn),
                    "rarity": skin.get("rarity", {}).get("name", ""),
                    "stattrak": st, "souvenir": souv,
                }
    with open("data/item_aliases.json", "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)
    print(f"生成 {len(aliases)} 条映射 → data/item_aliases.json")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: app/item_mapper.py**

```python
"""饰品名称映射器。"""
import json
from pathlib import Path


class ItemMapper:
    def __init__(self, data_path: str = "data/item_aliases.json"):
        self._path = Path(data_path)
        self._by_name: dict = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        if not self._path.exists():
            raise FileNotFoundError(f"映射表未找到: {self._path}。请先运行 scripts/build_item_map.py")
        with open(self._path, "r", encoding="utf-8") as f:
            self._by_name = json.load(f)
        self._loaded = True

    def get(self, market_hash_name: str) -> dict | None:
        self._ensure_loaded()
        return self._by_name.get(market_hash_name)

    def exists(self, market_hash_name: str) -> bool:
        self._ensure_loaded()
        return market_hash_name in self._by_name

    def search(self, query: str, limit: int = 20) -> list[dict]:
        self._ensure_loaded()
        q = query.lower()
        results = []
        for name, info in self._by_name.items():
            if q in name.lower() or q in info.get("weapon", "").lower():
                results.append({"market_hash_name": name, **info})
            if len(results) >= limit:
                break
        return results


item_mapper = ItemMapper()
```

- [ ] **Step 3: tests/test_item_mapper.py**

```python
import pytest
from app.item_mapper import ItemMapper


@pytest.fixture
def mapper():
    m = ItemMapper.__new__(ItemMapper)
    m._path = None
    m._loaded = True
    m._by_name = {
        "AK-47 | Redline (Field-Tested)": {
            "name": "AK-47 | Redline", "weapon": "AK-47",
            "wear": "Field-Tested", "wear_cn": "久经沙场", "rarity": "Classified",
        },
        "AWP | Dragon Lore (Factory New)": {
            "name": "AWP | Dragon Lore", "weapon": "AWP",
            "wear": "Factory New", "wear_cn": "崭新出厂", "rarity": "Covert",
        },
    }
    return m


def test_exists_known(mapper):
    assert mapper.exists("AK-47 | Redline (Field-Tested)") is True


def test_exists_unknown(mapper):
    assert mapper.exists("Fake (FN)") is False


def test_search_by_weapon(mapper):
    results = mapper.search("AWP")
    assert len(results) == 1


def test_search_case_insensitive(mapper):
    assert len(mapper.search("redline")) >= 1


def test_get_returns_info(mapper):
    info = mapper.get("AK-47 | Redline (Field-Tested)")
    assert info["wear_cn"] == "久经沙场"
```

- [ ] **Step 4: Run tests → PASS**

```bash
python -m pytest tests/test_item_mapper.py -v
```

- [ ] **Step 5: 运行脚本生成真实映射表**

```bash
python scripts/build_item_map.py
```

- [ ] **Step 6: Commit**

```bash
git add scripts/build_item_map.py app/item_mapper.py tests/test_item_mapper.py data/ && git commit -m "feat: item name mapper — ByMykel API integration + search"
```

---

## Phase 4: 监控列表 Web 管理

### Task 8: Dashboard + Watchlist CRUD

**Files:**
- Create: `app/routes/dashboard.py`
- Create: `app/routes/watchlist.py`
- Create: `tests/test_watchlist.py`

- [ ] **Step 1: app/routes/dashboard.py**

```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.database import get_db
from app.routes.deps import login_required
from app.models import WatchlistItem, AlertLog

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user

    watchlist_count = (await db.execute(
        select(func.count(WatchlistItem.id)).where(
            WatchlistItem.user_id == user.id, WatchlistItem.enabled == True
        )
    )).scalar()

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    alert_count = (await db.execute(
        select(func.count(AlertLog.id)).where(
            AlertLog.user_id == user.id, AlertLog.sent_at >= today
        )
    )).scalar()

    return request.app.state.templates.TemplateResponse(
        "dashboard.html.j2",
        {"request": request, "user": user, "watchlist_count": watchlist_count or 0, "alert_count": alert_count or 0},
    )
```

- [ ] **Step 2: app/routes/watchlist.py**

```python
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.routes.deps import login_required
from app.models import WatchlistItem
from app.item_mapper import item_mapper

router = APIRouter()


@router.get("/watchlist", response_class=HTMLResponse)
async def list_watchlist(request: Request, db: AsyncSession = Depends(get_db)):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.created_at.desc())
    )
    items = result.scalars().all()
    return request.app.state.templates.TemplateResponse(
        "watchlist.html.j2", {"request": request, "user": user, "items": items}
    )


@router.post("/watchlist/add")
async def add_item(
    request: Request, item_name: str = Form(...),
    target_price: float = Form(...), mode: int = Form(1),
    db: AsyncSession = Depends(get_db),
):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user
    results = item_mapper.search(item_name, limit=10)
    if not results:
        result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.created_at.desc())
        )
        items = result.scalars().all()
        return request.app.state.templates.TemplateResponse(
            "watchlist.html.j2", {"request": request, "user": user, "items": items, "error": f"未找到: {item_name}"}
        )
    market_name = results[0]["market_hash_name"]
    item = WatchlistItem(user_id=user.id, market_hash_name=market_name, target_price=target_price, mode=mode)
    db.add(item)
    await db.commit()
    return RedirectResponse(url="/watchlist", status_code=302)


@router.post("/watchlist/{item_id}/toggle")
async def toggle_item(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if item:
        item.enabled = not item.enabled
        await db.commit()
    return RedirectResponse(url="/watchlist", status_code=302)


@router.post("/watchlist/{item_id}/delete")
async def delete_item(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
    return RedirectResponse(url="/watchlist", status_code=302)
```

- [ ] **Step 3: 注册新路由到 main.py**

```python
from app.routes import dashboard, watchlist
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(watchlist.router, tags=["watchlist"])
```

- [ ] **Step 4: tests/test_watchlist.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_watchlist_requires_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/watchlist", follow_redirects=False)
        assert response.status_code == 302
```

- [ ] **Step 5: Commit**

```bash
git add app/routes/dashboard.py app/routes/watchlist.py tests/test_watchlist.py app/main.py && git commit -m "feat: dashboard + watchlist CRUD with item search"
```

---

## Phase 5: 爬虫 + 告警引擎 + 通知

### Task 9: 爬虫实现

**Files:**
- Create: `scheduler/crawlers/__init__.py`
- Create: `scheduler/crawlers/csqaq.py`
- Create: `scheduler/crawlers/steamdt.py`
- Create: `scheduler/crawlers/steam_inventory.py`

- [ ] **Step 1: scheduler/crawlers/csqaq.py**

```python
"""CSQAQ 价格爬虫 — asyncio + httpx。"""
import asyncio, logging, httpx
from typing import Optional

logger = logging.getLogger(__name__)


async def fetch_price(name: str, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> Optional[float]:
    async with sem:
        try:
            resp = await client.get(
                "https://www.csgoaq.com/api/search",
                params={"keyword": name}, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", [])
            if items:
                price = items[0].get("price") or items[0].get("min_price")
                return float(price) if price else None
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"CSQAQ 429, 等待 60s"); await asyncio.sleep(60)
            return None
        except httpx.TimeoutException:
            logger.warning(f"CSQAQ timeout: {name}"); return None
        except Exception as e:
            logger.error(f"CSQAQ error: {name} — {e}"); return None


async def fetch_prices(items: list[str], timeout: int = 15, max_concurrent: int = 5) -> dict[str, Optional[float]]:
    sem = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = {name: fetch_price(name, client, sem) for name in items}
        results = {}
        for name, task in tasks.items():
            results[name] = await task
    return results
```

- [ ] **Step 2: scheduler/crawlers/steamdt.py — 同理，endpoint 不同**

```python
"""SteamDT 价格爬虫。"""
import asyncio, logging, httpx
from typing import Optional

logger = logging.getLogger(__name__)


async def fetch_price(name: str, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> Optional[float]:
    async with sem:
        try:
            resp = await client.get(
                "https://www.steamdt.com/api/price",
                params={"name": name}, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            price = data.get("price") or data.get("current_price")
            return float(price) if price else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"SteamDT 429"); await asyncio.sleep(60)
            return None
        except Exception:
            return None


async def fetch_prices(items: list[str], timeout: int = 15, max_concurrent: int = 5) -> dict[str, Optional[float]]:
    sem = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = {name: fetch_price(name, client, sem) for name in items}
        return {name: await task for name, task in tasks.items()}
```

- [ ] **Step 3: scheduler/crawlers/steam_inventory.py**

```python
"""Steam 公开库存拉取。"""
import logging, httpx

logger = logging.getLogger(__name__)


async def fetch_inventory(steam_id: str) -> list[dict]:
    url = f"https://steamcommunity.com/inventory/{steam_id}/730/2"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params={"l": "schinese", "count": 2000})
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                return []
            items = []
            descriptions = {d.get("classid"): d for d in data.get("descriptions", [])}
            for asset in data.get("assets", []):
                desc = descriptions.get(asset.get("classid"))
                if desc:
                    items.append({
                        "asset_id": asset.get("assetid", ""),
                        "market_hash_name": desc.get("market_hash_name", ""),
                        "image_url": f"https://steamcommunity-a.akamaihd.net/economy/image/{desc.get('icon_url', '')}",
                        "tradable": asset.get("tradable", False),
                    })
            return items
    except Exception as e:
        logger.error(f"Steam inventory failed: {steam_id} — {e}")
        return []
```

- [ ] **Step 4: Commit**

```bash
git add scheduler/crawlers/ && git commit -m "feat: async crawlers — CSQAQ, SteamDT, Steam Inventory"
```

---

### Task 10: 告警引擎 + 通知

**Files:**
- Create: `scheduler/alerter.py`
- Create: `scheduler/notifier.py`
- Create: `tests/test_alerter.py`
- Create: `tests/test_notifier.py`

- [ ] **Step 1: 编写 tests/test_alerter.py → 失败 → 实现 scheduler/alerter.py**

```python
"""告警规则引擎 — 纯函数。"""


def check_mode_1(current_price: float, target_price: float | None) -> bool:
    """单品盯价：当前价 ≤ 目标价 → 触发。"""
    if target_price is None:
        return False
    return current_price <= target_price


def check_mode_2(current_price: float, cost_price: float | None, threshold_pct: float = 5.0) -> bool:
    """持仓组合：涨跌幅 ≥ 阈值% → 触发。"""
    if cost_price is None or cost_price <= 0:
        return False
    return abs(current_price - cost_price) / cost_price * 100 >= threshold_pct


def check_mode_3(price_changes: dict[str, float], top_n: int = 5) -> dict:
    """市场扫描：Top N 涨/跌。"""
    sorted_items = sorted(price_changes.items(), key=lambda x: x[1], reverse=True)
    return {"top_gainers": sorted_items[:top_n], "top_losers": sorted_items[-top_n:]}
```

- [ ] **Step 2: 测试 — 所有 alerter 测试应 PASS**

```bash
python -m pytest tests/test_alerter.py -v
```

- [ ] **Step 3: scheduler/notifier.py**

```python
"""Server酱 通知推送。"""
import asyncio, logging, httpx
from app.encryption import decrypt_value

logger = logging.getLogger(__name__)


async def send(send_key_encrypted: str, title: str, content: str) -> bool:
    send_key = decrypt_value(send_key_encrypted)
    url = f"https://sctapi.ftqq.com/{send_key}.send"
    for attempt in range(2):  # 1 次 + 1 次重试
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json={"title": title, "desp": content})
                if resp.json().get("code") == 0:
                    return True
        except Exception as e:
            logger.error(f"Server酱 error (attempt {attempt+1}): {e}")
        if attempt < 1:
            await asyncio.sleep(5)
    return False


def format_price_alert(market_hash_name: str, current: float, target: float, platform: str) -> tuple[str, str]:
    change = (current - target) / target * 100
    title = f"[CS2 告警] {market_hash_name}"
    content = f"{market_hash_name}\n\n当前: ¥{current:.2f} | 目标: ¥{target:.2f} | {'跌幅' if change < 0 else '价差'}: {change:+.1f}%\n平台: {platform}"
    return title, content
```

- [ ] **Step 4: tests/test_notifier.py — 格式化函数测试**

```python
from scheduler.notifier import format_price_alert


def test_format_shows_decline():
    title, content = format_price_alert("AK-47 | Redline (FT)", 85.0, 100.0, "CSQAQ")
    assert "跌幅" in content
    assert "¥85.00" in content
```

- [ ] **Step 5: Run tests → PASS**

```bash
python -m pytest tests/test_alerter.py tests/test_notifier.py -v
```

- [ ] **Step 6: Commit**

```bash
git add scheduler/alerter.py scheduler/notifier.py tests/test_alerter.py tests/test_notifier.py && git commit -m "feat: alert engine (3 modes) + Server酱 notifier"
```

---

## Phase 6: 独立调度进程

### Task 11: Scheduler 主进程 + 定时任务编排

**Files:**
- Create: `scheduler/main.py`
- Create: `scheduler/tasks.py`

- [ ] **Step 1: scheduler/tasks.py — 爬取 + 告警 + 清理主逻辑**

```python
"""定时任务编排。"""
import asyncio, logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import WatchlistItem, User, PriceSnapshot, AlertLog
from scheduler.crawlers import csqaq, steamdt
from scheduler.alerter import check_mode_1, check_mode_2
from scheduler.notifier import send, format_price_alert

logger = logging.getLogger(__name__)


async def run_price_crawl():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WatchlistItem.market_hash_name).where(WatchlistItem.enabled == True).distinct()
        )
        all_items = [row[0] for row in result.all()]
        logger.info(f"爬取 {len(all_items)} 件饰品")

        # CSQAQ 主源
        csqaq_prices = await csqaq.fetch_prices(all_items)
        # Fallback: CSQAQ 失败的项用 SteamDT 补
        failed = [n for n, p in csqaq_prices.items() if p is None]
        steamdt_prices = await steamdt.fetch_prices(failed) if failed else {}

        now = datetime.now(timezone.utc)
        snapshots = []
        for name in all_items:
            price = csqaq_prices.get(name)
            platform = "csqaq"
            if price is None:
                price = steamdt_prices.get(name)
                platform = "steamdt"
            if price is not None:
                snapshots.append(PriceSnapshot(market_hash_name=name, platform=platform, price=price, timestamp=now))

        if snapshots:
            db.add_all(snapshots)
            await db.commit()
            logger.info(f"写入 {len(snapshots)} 条快照")

    await run_alert_check()


async def run_alert_check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(WatchlistItem).where(WatchlistItem.enabled == True))
        items = result.scalars().all()
        alerts = 0
        for item in items:
            price_result = await db.execute(
                select(PriceSnapshot.price, PriceSnapshot.platform)
                .where(PriceSnapshot.market_hash_name == item.market_hash_name)
                .order_by(PriceSnapshot.timestamp.desc()).limit(1)
            )
            latest = price_result.first()
            if not latest:
                continue
            current_price, platform = latest
            triggered, message = False, ""

            if item.mode == 1 and check_mode_1(current_price, item.target_price):
                triggered, message = True, f"{format_price_alert(item.market_hash_name, current_price, item.target_price, platform)[1]}"
            elif item.mode == 2 and check_mode_2(current_price, item.cost_price, item.threshold_pct or 5.0):
                change = (current_price - item.cost_price) / item.cost_price * 100
                message = f"[CS2 持仓告警]\n{item.market_hash_name}\n当前: ¥{current_price:.2f} | 成本: ¥{item.cost_price:.2f} | {'涨幅' if change>0 else '跌幅'}: {change:+.1f}%"
                triggered = True

            if triggered:
                user_result = await db.execute(select(User).where(User.id == item.user_id))
                user = user_result.scalar_one_or_none()
                success = False
                if user and user.server_chan_key_encrypted:
                    success = await send(user.server_chan_key_encrypted, f"[CS2 告警] {item.market_hash_name}", message)
                db.add(AlertLog(user_id=item.user_id, market_hash_name=item.market_hash_name, rule_type=item.mode, new_price=current_price, message=message, success=success))
                alerts += 1

        await db.commit()
        logger.info(f"告警: {alerts} 条触发")


async def run_daily_cleanup():
    """30 天前数据聚合为小时级别（实施时完成具体 SQL）。"""
    logger.info("数据清理...")


async def run_daily_report():
    """每日持仓日报推送（实施时完成）。"""
    logger.info("日报生成...")
```

- [ ] **Step 2: scheduler/main.py — 独立进程入口**

```python
"""独立调度进程。运行: python -m scheduler.main"""
import asyncio, logging
from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from scheduler.tasks import run_price_crawl, run_daily_cleanup, run_daily_report
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("scheduler")


async def main():
    scheduler = AsyncScheduler()
    await scheduler.add_schedule(run_price_crawl, IntervalTrigger(seconds=settings.crawler_interval_seconds), id="price_crawl")
    await scheduler.add_schedule(run_daily_cleanup, CronTrigger(hour=settings.retention_cleanup_hour, minute=0), id="daily_cleanup")
    await scheduler.add_schedule(run_daily_report, CronTrigger(hour=settings.daily_report_hour, minute=0), id="daily_report")
    await scheduler.start_in_background()
    logger.info("调度器已启动")
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Commit**

```bash
git add scheduler/main.py scheduler/tasks.py && git commit -m "feat: standalone scheduler — crawl + alert + cleanup + report pipeline"
```

---

## Phase 7: 模板 + 前端

### Task 12: Jinja2 模板 + 样式

**Files:**
- Create: `app/static/style.css`
- Create: `app/templates/dashboard.html.j2`
- Create: `app/templates/watchlist.html.j2`

（base/login/register 已在 Task 5 创建）

- [ ] **Step 1: app/static/style.css — 极简暗色主题**

```css
:root { --bg:#0d1117;--card:#161b22;--border:#30363d;--text:#c9d1d9;--accent:#58a6ff;--green:#3fb950;--red:#f85149;--orange:#d2991d; }
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--text)}
nav{background:var(--card);padding:12px 24px;border-bottom:1px solid var(--border)}
nav a{color:var(--accent);text-decoration:none;margin-right:16px}
main{max-width:960px;margin:24px auto;padding:0 16px}
.alert{padding:12px 16px;border-radius:6px;margin-bottom:16px}
.alert-error{background:#f8514922;border:1px solid var(--red);color:var(--red)}
.alert-success{background:#3fb95022;border:1px solid var(--green);color:var(--green)}
table{width:100%;border-collapse:collapse;margin:16px 0}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border)}
th{color:#8b949e;font-weight:600;font-size:13px}
input,select,button{padding:8px 12px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font-size:14px}
button{background:#238636;border-color:var(--green);color:#fff;cursor:pointer}
button:hover{background:#2ea043}
button.danger{background:#da3633;border-color:var(--red)}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:16px}
.stats{display:flex;gap:16px;margin-bottom:24px}
.stat-box{flex:1;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px;text-align:center}
.stat-box .value{font-size:28px;font-weight:700;margin:8px 0}
.stat-box .label{color:#8b949e;font-size:13px}
.price-up{color:var(--green)}
.price-down{color:var(--red)}
```

- [ ] **Step 2: 挂载静态文件到 main.py**

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

- [ ] **Step 3: dashboard.html.j2**

```html
{% extends "base.html.j2" %}
{% block title %}仪表盘 - CS2 Monitor{% endblock %}
{% block content %}
<h1>仪表盘</h1>
<div class="stats">
    <div class="stat-box"><div class="label">监控饰品</div><div class="value">{{ watchlist_count }}</div></div>
    <div class="stat-box"><div class="label">今日告警</div><div class="value">{{ alert_count }}</div></div>
</div>
{% endblock %}
```

- [ ] **Step 4: watchlist.html.j2**

```html
{% extends "base.html.j2" %}
{% block title %}监控列表 - CS2 Monitor{% endblock %}
{% block content %}
<h1>监控列表</h1>
<div class="card">
    <form method="post" action="/watchlist/add">
        <input name="item_name" placeholder="搜索饰品名（如 AK-47 红线）" required style="width:300px">
        <input name="target_price" type="number" step="0.01" placeholder="目标价 ¥" required>
        <select name="mode"><option value="1">模式一：盯价</option><option value="2">模式二：持仓</option></select>
        <button type="submit">添加监控</button>
    </form>
</div>
<table>
    <tr><th>饰品</th><th>目标价</th><th>模式</th><th>状态</th><th>操作</th></tr>
    {% for item in items %}
    <tr>
        <td>{{ item.market_hash_name }}</td>
        <td>¥{{ "%.2f"|format(item.target_price) if item.target_price else '-' }}</td>
        <td>{{ ['','盯价','持仓','扫描'][item.mode] }}</td>
        <td>{{ '启用' if item.enabled else '停用' }}</td>
        <td>
            <form method="post" action="/watchlist/{{ item.id }}/toggle" style="display:inline">
                <button type="submit">{{ '停用' if item.enabled else '启用' }}</button>
            </form>
            <form method="post" action="/watchlist/{{ item.id }}/delete" style="display:inline">
                <button type="submit" class="danger">删除</button>
            </form>
        </td>
    </tr>
    {% endfor %}
</table>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add app/static/ app/templates/ app/main.py && git commit -m "feat: Jinja2 templates + dark theme CSS"
```

---

## Phase 8: 部署配置

### Task 13: Caddy + systemd

**Files:**
- Create: `deploy/caddy/Caddyfile`
- Create: `deploy/systemd/cs2-monitor-web.service`
- Create: `deploy/systemd/cs2-monitor-scheduler.service`

```ini
# deploy/systemd/cs2-monitor-web.service
[Unit]
Description=CS2 Monitor Web Server
After=network.target mysql.service

[Service]
User=cs2monitor
WorkingDirectory=/opt/cs2-monitor
ExecStart=/opt/cs2-monitor/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```ini
# deploy/systemd/cs2-monitor-scheduler.service
[Unit]
Description=CS2 Monitor Scheduler
After=network.target mysql.service

[Service]
User=cs2monitor
WorkingDirectory=/opt/cs2-monitor
ExecStart=/opt/cs2-monitor/venv/bin/python -m scheduler.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```
# deploy/caddy/Caddyfile
cs2monitor.example.com {
    reverse_proxy localhost:8000
    encode gzip
}
```

- [ ] **Commit**

```bash
git add deploy/ && git commit -m "feat: deployment config — Caddy reverse proxy + systemd units"
```

---

## 实施顺序

```
Phase 1 (骨架) → Phase 2 (认证) → Phase 3 (映射) → Phase 4 (监控 CRUD)
                                                           │
Phase 5 (爬虫) ←── Phase 6 (调度器)                       │
                     │                                     │
                     └── Phase 7 (模板) ←──────────────────┘
                           │
Phase 8 (部署) ←───────────┘
```

### 并行机会

- Phase 4 (Web CRUD) 和 Phase 5 (爬虫) 可以并行 — 互相独立
- Phase 6 (调度器) 依赖 Phase 5 的爬虫实现
- Phase 7 (模板) 可以在 Phase 4 之后立即开始

---

## 测试覆盖

| 模块 | 测试文件 | 优先 |
|------|----------|------|
| alerter.py | `test_alerter.py` | P0 — 核心逻辑 |
| notifier.py | `test_notifier.py` | P0 — 格式化 |
| item_mapper.py | `test_item_mapper.py` | P0 — 映射查詢 |
| auth.py | `test_auth.py` | P1 — 认证流程 |
| watchlist.py | `test_watchlist.py` | P1 — CRUD |
| crawlers | `test_crawlers.py` | P2 — mock 外部 API |

---

## NOT in Scope (本计划明确不做)

- WebSocket 实时推送
- 价格走势图（charts.js）
- Docker 部署
- OpenID/OAuth 登录
- 企微机器人
- 邮件通知
- 管理后台 UI（用户管理）
