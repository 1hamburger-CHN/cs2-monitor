"""Route blueprints for the CS2 Monitor application."""
from app.routes import auth, deps, dashboard, watchlist, user_settings

__all__ = ["auth", "deps", "dashboard", "watchlist", "user_settings"]
