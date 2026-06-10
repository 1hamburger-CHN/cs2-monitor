"""JSON API routes for Vue PWA frontend. Prefix: /api/v1"""
import datetime
import json
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from passlib.context import CryptContext
from app.config import settings
from app.database import get_db
from app.routes.deps import get_current_user, api_login_required
from app.models import User, WatchlistItem, PriceSnapshot, AlertLog, InviteCode
from app.item_mapper import item_mapper
from app.encryption import encrypt_value

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Image URL cache (populated by scheduler crawler)
IMG_CACHE_FILE = Path("data/img_cache.json")

def _load_img_cache():
    if IMG_CACHE_FILE.exists():
        return json.loads(IMG_CACHE_FILE.read_text())
    return {}

def _get_img_url(market_hash_name: str) -> str | None:
    return _load_img_cache().get(market_hash_name)


# Pydantic schemas

class LoginBody(BaseModel):
    username: str
    password: str

class RegisterBody(BaseModel):
    username: str
    password: str
    invite_code: str

class AddWatchlistBody(BaseModel):
    item_name: str
    target_price: float = 0
    mode: int = 1

class UpdateWatchlistBody(BaseModel):
    target_price: float | None = None
    mode: int | None = None
    enabled: bool | None = None

class SaveSettingsBody(BaseModel):
    server_chan_key: str | None = None
    steam_id: str | None = None
    steam_api_key: str | None = None
    preferred_source: str | None = None

class PushSubscriptionBody(BaseModel):
    endpoint: str
    keys: dict


# auth

@router.get("/me")
async def api_me(user: User = Depends(api_login_required)):
    return {"id": user.id, "username": user.username}


@router.post("/auth/login")
async def api_login(body: LoginBody, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username.strip()))
    user = result.scalar_one_or_none()
    if user is None or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(401, "wrong username or password")
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return {"id": user.id, "username": user.username}


@router.post("/auth/register")
async def api_register(body: RegisterBody, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InviteCode).where(InviteCode.code == body.invite_code.strip().upper())
    )
    code = result.scalar_one_or_none()
    if code is None or not code.is_valid:
        raise HTTPException(400, "invalid or expired invite code")

    result = await db.execute(select(User).where(User.username == body.username.strip()))
    if result.scalar_one_or_none():
        raise HTTPException(400, "username already taken")

    user = User(username=body.username.strip(), password_hash=pwd_context.hash(body.password))
    db.add(user)
    code.used_count += 1
    await db.commit()

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return {"id": user.id, "username": user.username}


@router.post("/auth/logout")
async def api_logout(request: Request):
    request.session.clear()
    return {"ok": True}


# dashboard

@router.get("/dashboard")
async def api_dashboard(user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    wc = (await db.execute(
        select(func.count(WatchlistItem.id)).where(
            WatchlistItem.user_id == user.id, WatchlistItem.enabled == True
        )
    )).scalar() or 0

    today = datetime.datetime.now(datetime.timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    ac = (await db.execute(
        select(func.count(AlertLog.id)).where(
            AlertLog.user_id == user.id, AlertLog.sent_at >= today
        )
    )).scalar() or 0

    items_result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.created_at.desc())
    )
    items = items_result.scalars().all()

    item_list = []
    portfolio_value = 0.0
    has_any_price = False
    for item in items:
        price_result = await db.execute(
            select(PriceSnapshot.price, PriceSnapshot.platform)
            .where(PriceSnapshot.market_hash_name == item.market_hash_name)
            .order_by(PriceSnapshot.timestamp.desc()).limit(1)
        )
        latest = price_result.first()
        item_list.append({
            "id": item.id,
            "market_hash_name": item.market_hash_name,
            "target_price": item.target_price,
            "mode": item.mode,
            "enabled": item.enabled,
            "latest_price": latest[0] if latest else None,
            "platform": latest[1] if latest else None,
            "img_url": _get_img_url(item.market_hash_name),
        })
        if latest:
            has_any_price = True
            portfolio_value += latest[0] * (item.quantity or 1)

    # Last crawl time for countdown timer
    last_crawl = (await db.execute(
        select(func.max(PriceSnapshot.timestamp))
    )).scalar()

    return {
        "watchlist_count": wc,
        "alert_count": ac,
        "portfolio_value": round(portfolio_value, 2) if has_any_price else None,
        "last_crawl_time": last_crawl.isoformat() + "Z" if last_crawl else None,
        "crawl_interval_s": settings.crawler_interval_seconds,
        "items": item_list,
    }


# watchlist CRUD

@router.get("/watchlist")
async def api_list_watchlist(user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.created_at.desc())
    )
    items = result.scalars().all()
    return [
        {
            "id": i.id,
            "market_hash_name": i.market_hash_name,
            "target_price": i.target_price,
            "mode": i.mode,
            "enabled": i.enabled,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in items
    ]


@router.get("/watchlist/{item_id}")
async def api_get_watchlist_item(item_id: int, user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "not found")

    price_result = await db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.market_hash_name == item.market_hash_name)
        .order_by(PriceSnapshot.timestamp.desc()).limit(4)
    )
    prices = price_result.scalars().all()

    price_map = {}
    for p in prices:
        platform = p.platform
        if platform in ("csqaq", "buff"):
            if "buff" not in price_map:
                price_map["buff"] = p.price
        elif platform in ("yyyp", "c5", "steam"):
            price_map[platform] = p.price

    return {
        "id": item.id,
        "market_hash_name": item.market_hash_name,
        "target_price": item.target_price,
        "mode": item.mode,
        "enabled": item.enabled,
        "prices": price_map,
        "img_url": _get_img_url(item.market_hash_name),
    }


@router.post("/watchlist")
async def api_add_watchlist(body: AddWatchlistBody, user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    results = item_mapper.search(body.item_name, limit=10)
    if not results:
        raise HTTPException(400, f"item not found: {body.item_name}")

    market_name = results[0]["market_hash_name"]
    target = body.target_price if body.target_price > 0 else None
    item = WatchlistItem(
        user_id=user.id,
        market_hash_name=market_name,
        target_price=target,
        mode=body.mode,
    )
    db.add(item)
    await db.commit()
    return {"id": item.id, "market_hash_name": item.market_hash_name, "mode": item.mode}


@router.patch("/watchlist/{item_id}")
async def api_update_watchlist(item_id: int, body: UpdateWatchlistBody, user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "not found")

    if body.target_price is not None:
        item.target_price = body.target_price
    if body.mode is not None:
        item.mode = body.mode
    if body.enabled is not None:
        item.enabled = body.enabled
    await db.commit()
    return {"id": item.id, "ok": True}


@router.delete("/watchlist/{item_id}")
async def api_delete_watchlist(item_id: int, user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "not found")
    await db.delete(item)
    await db.commit()
    return {"ok": True}


# item search

@router.get("/items/search")
async def api_search_items(q: str = "", limit: int = 20):
    results = item_mapper.search(q, limit=limit)
    return [
        {
            "market_hash_name": r["market_hash_name"],
            "cn_name": r.get("cn_name", r["market_hash_name"]),
            "weapon": r.get("weapon", ""),
            "wear_cn": r.get("wear_cn", ""),
            "img_url": _get_img_url(r["market_hash_name"]),
        }
        for r in results
    ]


# alert history

@router.get("/alerts")
async def api_alerts(user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db), page: int = 1, limit: int = 50):
    offset = (page - 1) * limit
    total = (await db.execute(
        select(func.count(AlertLog.id)).where(AlertLog.user_id == user.id)
    )).scalar() or 0

    result = await db.execute(
        select(AlertLog)
        .where(AlertLog.user_id == user.id)
        .order_by(AlertLog.sent_at.desc())
        .offset(offset).limit(limit)
    )
    return {
        "items": [
            {
                "id": a.id,
                "message": a.message,
                "sent_at": a.sent_at.isoformat() if a.sent_at else None,
                "rule_type": a.rule_type,
                "market_hash_name": a.market_hash_name,
            }
            for a in result.scalars().all()
        ],
        "total": total,
    }


# user settings

@router.get("/settings")
async def api_get_settings(user: User = Depends(api_login_required)):
    masked = (user.server_chan_key_encrypted or "")[:8]
    if masked:
        masked += "****"
    return {
        "server_chan_key_masked": masked,
        "steam_id": user.steam_id or "",
        "preferred_source": user.preferred_source or "csqaq",
    }


@router.put("/settings")
async def api_save_settings(body: SaveSettingsBody, user: User = Depends(api_login_required), db: AsyncSession = Depends(get_db)):
    if body.server_chan_key:
        user.server_chan_key_encrypted = encrypt_value(body.server_chan_key.strip())
    if body.steam_id is not None:
        user.steam_id = body.steam_id.strip()
    if body.steam_api_key:
        user.steam_api_key_encrypted = encrypt_value(body.steam_api_key.strip())
    if body.preferred_source:
        user.preferred_source = body.preferred_source
    await db.commit()
    return {"ok": True}


# web push

@router.post("/push/subscribe")
async def api_push_subscribe(body: PushSubscriptionBody, user: User = Depends(api_login_required)):
    sub_path = Path("data/push_subscriptions.json")
    sub_path.parent.mkdir(parents=True, exist_ok=True)
    subs = {}
    if sub_path.exists():
        subs = json.loads(sub_path.read_text())
    subs[str(user.id)] = {"endpoint": body.endpoint, "keys": body.keys}
    sub_path.write_text(json.dumps(subs, indent=2))
    return {"ok": True}
