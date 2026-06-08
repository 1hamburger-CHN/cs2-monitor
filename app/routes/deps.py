"""Route dependency injection."""
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
