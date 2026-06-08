"""Watchlist tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_watchlist_page_requires_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/watchlist", follow_redirects=False)
        assert response.status_code == 302


@pytest.mark.asyncio
async def test_dashboard_page_requires_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
