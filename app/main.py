"""FastAPI application entry point."""
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
