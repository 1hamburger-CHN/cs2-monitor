import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db


@pytest_asyncio.fixture(scope="function")
async def client():
    """AsyncClient against the FastAPI app (no real server)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── SPA / static file tests ──

@pytest.mark.asyncio
async def test_spa_root_serves_index(client):
    """SPA serves index.html at the root."""
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_spa_fallback_serves_index_for_page_routes(client):
    """SPA fallback middleware serves index.html for non-API paths like /login."""
    response = await client.get("/login")
    assert response.status_code == 200


# ── API auth guard tests (no DB needed) ──

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
async def test_api_watchlist_requires_auth(client):
    response = await client.get("/api/v1/watchlist")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_dashboard_requires_auth(client):
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 401


# ── DB-dependent tests ──

@pytest.mark.asyncio
async def test_api_login_wrong_password(client):
    """Login with wrong credentials returns 401 (mock DB session)."""
    # db.execute is async → returns coroutine → awaited → result
    # result.scalar_one_or_none is sync → returns None (no user found)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    # override must match the original signature: async generator that yields
    async def mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = mock_get_db
    try:
        response = await client.post("/api/v1/auth/login", json={
            "username": "nonexistent_user_xyz", "password": "wrong"
        })
        assert response.status_code == 401
    finally:
        del app.dependency_overrides[get_db]
