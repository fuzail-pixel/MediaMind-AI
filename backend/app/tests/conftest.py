# backend/app/tests/conftest.py

import pytest
import pytest_asyncio
import uuid
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token


def make_engine():
    db_name = f"test_{uuid.uuid4().hex}.db"
    url = f"sqlite+aiosqlite:///./{db_name}"
    engine = create_async_engine(
        url,
        connect_args={"check_same_thread": False}
    )
    return engine, db_name


@pytest_asyncio.fixture
async def test_db():
    engine, db_name = make_engine()
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine, SessionLocal, db_name
    await engine.dispose()
    if os.path.exists(db_name):
        os.remove(db_name)


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user and return it."""
    from app.models.user import User
    engine, SessionLocal, db_name = test_db
    async with SessionLocal() as session:
        user = User(
            google_id  = f"google_{uuid.uuid4().hex}",
            email      = f"test_{uuid.uuid4().hex}@gmail.com",
            full_name  = "Test User",
            avatar_url = "https://example.com/avatar.jpg",
            is_active  = True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def auth_token(test_user):
    """Create a valid JWT token for the test user."""
    return create_access_token({"sub": str(test_user.id)})


@pytest_asyncio.fixture
async def client(test_db, test_user, auth_token):
    """Authenticated HTTP test client."""
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

    # Override auth dependency to return test user
    from app.core.security import get_current_user
    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db]           = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {auth_token}"}
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(test_db, test_user):
    """Direct DB session — shares same DB as client fixture."""
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

    from app.core.security import get_current_user
    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db]           = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with SessionLocal() as session:
        yield session

    app.dependency_overrides.clear()