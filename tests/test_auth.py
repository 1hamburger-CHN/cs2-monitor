"""Auth system tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_page_loads(client):
    response = await client.get("/register")
    assert response.status_code == 200
    assert "注册" in response.text


@pytest.mark.asyncio
async def test_login_page_loads(client):
    response = await client.get("/login")
    assert response.status_code == 200
    assert "登录" in response.text


@pytest.mark.asyncio
async def test_register_requires_valid_invite_code(client):
    response = await client.post("/register", data={
        "username": "testuser", "password": "testpass123", "invite_code": "INVALID"
    })
    assert response.status_code == 200
    assert "邀请码无效" in response.text


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(client):
    response = await client.post("/login", data={
        "username": "nonexistent", "password": "wrong"
    })
    assert response.status_code == 200
    assert "用户名或密码错误" in response.text


@pytest.mark.asyncio
async def test_protected_page_redirects(client):
    response = await client.get("/watchlist", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]
