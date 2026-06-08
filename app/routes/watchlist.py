"""Watchlist management routes — CRUD for monitored items."""
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
    request: Request,
    item_name: str = Form(...),
    target_price: float = Form(...),
    mode: int = Form(1),
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
            "watchlist.html.j2",
            {"request": request, "user": user, "items": items, "error": f"未找到匹配的饰品: {item_name}"},
        )

    market_name = results[0]["market_hash_name"]
    item = WatchlistItem(
        user_id=user.id,
        market_hash_name=market_name,
        target_price=target_price,
        mode=mode,
    )
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
