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
async def client(test_db):
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


@pytest_asyncio.fixture
async def db_session(test_db):
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

    async with SessionLocal() as session:
        yield session

    app.dependency_overrides.clear()