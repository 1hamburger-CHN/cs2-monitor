"""Dashboard route — user home page."""
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
    )).scalar() or 0

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    alert_count = (await db.execute(
        select(func.count(AlertLog.id)).where(
            AlertLog.user_id == user.id, AlertLog.sent_at >= today
        )
    )).scalar() or 0

    return request.app.state.templates.TemplateResponse(
        "dashboard.html.j2",
        {"request": request, "user": user, "watchlist_count": watchlist_count, "alert_count": alert_count},
    )
