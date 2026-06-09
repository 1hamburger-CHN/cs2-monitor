"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.config import settings
from app.routes import auth, dashboard, watchlist, user_settings
from app.routes.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.templates = Jinja2Templates(directory="app/templates")
    yield


app = FastAPI(title="CS2 Monitor", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# ── API routes (always registered) ──
app.include_router(api_router, prefix="/api/v1")

# ── SPA (Vue PWA) frontend ──
spa_dir = Path(__file__).parent / "static" / "spa"
spa_built = spa_dir.is_dir()

if spa_built:
    # Mount SPA static files (handles MIME types correctly)
    app.mount("/", StaticFiles(directory=str(spa_dir), html=True), name="spa")

else:
    # Fallback: Jinja2 pages (when SPA not built)
    app.include_router(auth.router, tags=["auth"])
    app.include_router(dashboard.router, tags=["dashboard"])
    app.include_router(watchlist.router, tags=["watchlist"])
    app.include_router(user_settings.router, tags=["settings"])
