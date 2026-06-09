"""Auth system tests — API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_spa_serves_index(client):
    """SPA catch-all serves index.html for page routes."""
    response = await client.get("/login")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_me_requires_auth(client):
    response = await client.get("/api/v1/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_register_invalid_invite(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "testuser", "password": "testpass123", "invite_code": "INVALID"
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_api_login_wrong_password(client):
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent", "password": "wrong"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_watchlist_requires_auth(client):
    response = await client.get("/api/v1/watchlist")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_dashboard_requires_auth(client):
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 401
