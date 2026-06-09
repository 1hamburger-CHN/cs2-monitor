"""Watchlist API tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_api_watchlist_requires_auth(client):
    response = await client.get("/api/v1/watchlist")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_dashboard_requires_auth(client):
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_settings_requires_auth(client):
    response = await client.get("/api/v1/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_alerts_requires_auth(client):
    response = await client.get("/api/v1/alerts")
    assert response.status_code == 401
