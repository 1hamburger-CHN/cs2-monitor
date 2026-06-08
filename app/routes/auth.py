"""Authentication routes: register, login, logout."""
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
    # Validate invite code
    result = await db.execute(
        select(InviteCode).where(InviteCode.code == invite_code.strip().upper())
    )
    code = result.scalar_one_or_none()
    if code is None or not code.is_valid:
        return request.app.state.templates.TemplateResponse(
            "register.html.j2",
            {"request": request, "error": "邀请码无效或已过期"},
        )

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == username.strip()))
    if result.scalar_one_or_none():
        return request.app.state.templates.TemplateResponse(
            "register.html.j2",
            {"request": request, "error": "用户名已被占用"},
        )

    # Create user
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
