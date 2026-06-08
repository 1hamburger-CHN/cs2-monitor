"""User settings route — configure Steam ID, API Key, ServerChan SendKey, data source."""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.routes.deps import login_required
from app.encryption import encrypt_value

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user
    return request.app.state.templates.TemplateResponse(
        "settings.html.j2", {"request": request, "user": user}
    )


@router.post("/settings")
async def save_settings(
    request: Request,
    server_chan_key: str = Form(""),
    steam_id: str = Form(""),
    steam_api_key: str = Form(""),
    preferred_source: str = Form("csqaq"),
    db: AsyncSession = Depends(get_db),
):
    user = await login_required(request, db)
    if isinstance(user, HTMLResponse):
        return user

    if server_chan_key.strip():
        user.server_chan_key_encrypted = encrypt_value(server_chan_key.strip())
    if steam_id.strip():
        user.steam_id = steam_id.strip()
    if steam_api_key.strip():
        user.steam_api_key_encrypted = encrypt_value(steam_api_key.strip())
    user.preferred_source = preferred_source

    await db.commit()
    return request.app.state.templates.TemplateResponse(
        "settings.html.j2",
        {"request": request, "user": user, "success": "设置已保存"},
    )
