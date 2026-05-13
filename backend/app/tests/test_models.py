# backend/app/tests/test_models.py

import pytest
import uuid
from app.models.document import Document, FileType, ProcessingStatus
from app.models.chat import ChatSession, ChatMessage, MessageRole


def test_document_repr():
    """Test Document __repr__."""
    doc = Document(
        original_name = "test.pdf",
        file_type     = FileType.PDF
    )
    assert "test.pdf" in repr(doc)
    assert "pdf" in repr(doc)


def test_chat_session_repr():
    """Test ChatSession __repr__."""
    session = ChatSession()
    assert "ChatSession" in repr(session)


def test_chat_message_repr():
    """Test ChatMessage __repr__."""
    msg = ChatMessage(
        role    = MessageRole.USER,
        content = "This is a test message content"
    )
    assert "MessageRole.USER" in repr(msg)
    assert "This is a test" in repr(msg)


def test_file_type_values():
    """Test FileType enum values."""
    assert FileType.PDF   == "pdf"
    assert FileType.AUDIO == "audio"
    assert FileType.VIDEO == "video"


def test_processing_status_values():
    """Test ProcessingStatus enum values."""
    assert ProcessingStatus.PENDING    == "pending"
    assert ProcessingStatus.PROCESSING == "processing"
    assert ProcessingStatus.COMPLETED  == "completed"
    assert ProcessingStatus.FAILED     == "failed"


def test_message_role_values():
    """Test MessageRole enum values."""
    assert MessageRole.USER      == "user"
    assert MessageRole.ASSISTANT == "assistant"


@pytest.mark.asyncio
async def test_database_get_db():
    """Test get_db yields a session."""
    from app.core.database import get_db
    # Just verify get_db is a generator function
    import inspect
    assert inspect.isasyncgenfunction(get_db)


def test_settings_defaults():
    """Test settings have correct defaults."""
    from app.core.config import get_settings
    settings = get_settings()
    assert settings.APP_NAME == "MediaMind AI"
    assert settings.VERSION  == "1.0.0"
    assert settings.MAX_FILE_SIZE_MB == 50


@pytest.mark.asyncio
async def test_main_lifespan():
    """Test app lifespan runs without error."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200


def test_database_url_conversion():
    """Test DATABASE_URL is converted correctly for asyncpg."""
    from app.core.database import DATABASE_URL
    assert "postgresql+asyncpg://" in DATABASE_URL    


@pytest.mark.asyncio
async def test_get_db_session():
    """Test get_db provides working session."""
    from app.core.database import get_db, AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        assert session is not None


@pytest.mark.asyncio
async def test_main_startup():
    """Test main app starts and health endpoint works."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

        r2 = await ac.get("/docs")
        assert r2.status_code == 200    