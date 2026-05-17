# backend/app/tests/test_auth.py

import pytest
import pytest_asyncio
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token, decode_token, get_current_user, get_optional_user
from app.core.database import get_db
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear get_current_user override before each auth test."""
    app.dependency_overrides.pop(get_current_user, None)
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def raw_client(test_db):
    """Client with NO auth override — tests real auth behavior."""
    engine, SessionLocal, db_name = test_db

    async def override_get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# --- Security tests ---

def test_create_access_token():
    """Test JWT token creation."""
    token = create_access_token({"sub": "test-user-id"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token_valid():
    """Test decoding a valid JWT token."""
    token   = create_access_token({"sub": "test-user-id"})
    payload = decode_token(token)
    assert payload["sub"] == "test-user-id"


def test_decode_token_invalid():
    """Test decoding an invalid token raises 401."""
    with pytest.raises(HTTPException) as exc:
        decode_token("invalid.token.here")
    assert exc.value.status_code == 401


def test_decode_token_expired():
    """Test decoding an expired token raises 401."""
    from datetime import timedelta
    token = create_access_token({"sub": "test"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc:
        decode_token(token)
    assert exc.value.status_code == 401


# --- Auth route tests ---

@pytest.mark.asyncio
async def test_login_redirects(raw_client: AsyncClient):
    """Test login endpoint redirects to Google."""
    response = await raw_client.get("/api/v1/auth/login", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert "accounts.google.com" in response.headers["location"]


@pytest.mark.asyncio
async def test_logout(raw_client: AsyncClient):
    """Test logout returns success message."""
    response = await raw_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_me_no_token(raw_client: AsyncClient):
    """Test /auth/me without token returns 401 or 403."""
    response = await raw_client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_me_invalid_token(raw_client: AsyncClient):
    """Test /auth/me with invalid token returns 401."""
    response = await raw_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_valid_token(raw_client: AsyncClient, test_db):
    """Test /auth/me with valid token returns user info."""
    from app.models.user import User
    from sqlalchemy import select

    engine, SessionLocal, db_name = test_db

    async with SessionLocal() as session:
        user = User(
            google_id  = "google_valid_123",
            email      = "validuser@gmail.com",
            full_name  = "Valid User",
            avatar_url = "https://example.com/avatar.jpg",
            is_active  = True
        )
        session.add(user)
        await session.commit()
        # Fetch back to get the generated ID
        result  = await session.execute(select(User).where(User.email == "validuser@gmail.com"))
        saved   = result.scalar_one()
        user_id = str(saved.id)

    token    = create_access_token({"sub": user_id})
    response = await raw_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"]     == "validuser@gmail.com"
    assert data["full_name"] == "Valid User"


@pytest.mark.asyncio
async def test_get_me_inactive_user(raw_client: AsyncClient, test_db):
    """Test /auth/me with inactive user returns 401."""
    from app.models.user import User
    from sqlalchemy import select

    engine, SessionLocal, db_name = test_db

    async with SessionLocal() as session:
        user = User(
            google_id = "google_inactive_456",
            email     = "inactive@gmail.com",
            full_name = "Inactive User",
            is_active = False
        )
        session.add(user)
        await session.commit()
        result  = await session.execute(select(User).where(User.email == "inactive@gmail.com"))
        saved   = result.scalar_one()
        user_id = str(saved.id)

    token    = create_access_token({"sub": user_id})
    response = await raw_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_callback_bad_code(raw_client: AsyncClient):
    """Test callback with bad code returns 400."""
    with patch("app.api.routes.auth.httpx.AsyncClient") as mock_client:
        mock_response             = MagicMock()
        mock_response.status_code = 400
        mock_http                 = MagicMock()
        mock_http.post            = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client.return_value.__aexit__  = AsyncMock(return_value=False)

        response = await raw_client.get(
            "/api/v1/auth/callback?code=bad_code",
            follow_redirects=False
        )
    assert response.status_code in [400, 302, 307]


@pytest.mark.asyncio
async def test_auth_callback_success(raw_client: AsyncClient):
    """Test successful OAuth callback creates user and redirects."""
    mock_token_response             = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "google_token_123"}

    mock_user_response             = MagicMock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {
        "id"     : "google_new_user_999",
        "email"  : "brandnew@gmail.com",
        "name"   : "Brand New User",
        "picture": "https://example.com/pic.jpg"
    }

    with patch("app.api.routes.auth.httpx.AsyncClient") as mock_client:
        mock_http      = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_token_response)
        mock_http.get  = AsyncMock(return_value=mock_user_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client.return_value.__aexit__  = AsyncMock(return_value=False)

        response = await raw_client.get(
            "/api/v1/auth/callback?code=valid_code",
            follow_redirects=False
        )

    assert response.status_code in [302, 307]
    assert "token=" in response.headers["location"]


@pytest.mark.asyncio
async def test_auth_callback_existing_user(raw_client: AsyncClient, test_db):
    """Test callback with existing user updates info and redirects."""
    from app.models.user import User

    engine, SessionLocal, db_name = test_db

    async with SessionLocal() as session:
        user = User(
            google_id = "existing_google_id",
            email     = "existing@gmail.com",
            full_name = "Old Name",
            is_active = True
        )
        session.add(user)
        await session.commit()

    mock_token_response             = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "google_token_abc"}

    mock_user_response             = MagicMock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {
        "id"     : "existing_google_id",
        "email"  : "existing@gmail.com",
        "name"   : "Updated Name",
        "picture": "https://example.com/new_pic.jpg"
    }

    with patch("app.api.routes.auth.httpx.AsyncClient") as mock_client:
        mock_http      = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_token_response)
        mock_http.get  = AsyncMock(return_value=mock_user_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client.return_value.__aexit__  = AsyncMock(return_value=False)

        response = await raw_client.get(
            "/api/v1/auth/callback?code=existing_user_code",
            follow_redirects=False
        )

    assert response.status_code in [302, 307]
    assert "token=" in response.headers["location"]


@pytest.mark.asyncio
async def test_auth_callback_user_info_failure(raw_client: AsyncClient):
    """Token exchange succeeds but user info request fails."""
    mock_token_response             = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "google_token_123"}

    mock_user_response             = MagicMock()
    mock_user_response.status_code = 400

    with patch("app.api.routes.auth.httpx.AsyncClient") as mock_client:
        mock_http      = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_token_response)
        mock_http.get  = AsyncMock(return_value=mock_user_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client.return_value.__aexit__  = AsyncMock(return_value=False)

        response = await raw_client.get(
            "/api/v1/auth/callback?code=valid_but_no_user",
            follow_redirects=False
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_optional_user_no_credentials():
    """Test get_optional_user returns None with no credentials."""
    result = await get_optional_user(None, MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_get_optional_user_invalid_token_returns_none():
    """get_optional_user should return None for an invalid token."""
    creds  = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
    result = await get_optional_user(creds, MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_get_current_user_missing_sub(test_db):
    """get_current_user raises when token payload has no sub."""
    engine, SessionLocal, db_name = test_db
    token = create_access_token({})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    async with SessionLocal() as session:
        with pytest.raises(HTTPException) as exc:
            await get_current_user(creds, session)
    assert exc.value.status_code == 401


def test_user_repr():
    """Test User model repr."""
    from app.models.user import User
    user = User(email="test@gmail.com", google_id="123")
    assert "test@gmail.com" in repr(user)