# backend/app/tests/test_chat.py

import pytest
import io
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document, ProcessingStatus, FileType


async def create_completed_document(db: AsyncSession) -> str:
    """Helper — insert a completed document directly into test DB."""
    doc = Document(
        filename      = "test.pdf",
        original_name = "test.pdf",
        file_type     = FileType.PDF,
        file_size     = 1000,
        file_path     = "/fake/path/test.pdf",
        extracted_text= "This is a test document about Python programming and FastAPI development.",
        status        = ProcessingStatus.COMPLETED
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return str(doc.id)


@pytest.mark.asyncio
async def test_ask_question_document_not_ready(client: AsyncClient, db_session: AsyncSession):
    """Test asking question on pending document returns 400."""
    doc = Document(
        filename      = "pending.pdf",
        original_name = "pending.pdf",
        file_type     = FileType.PDF,
        file_size     = 1000,
        file_path     = "/fake/path/pending.pdf",
        status        = ProcessingStatus.PENDING
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    response = await client.post(
        "/api/v1/chat/ask",
        json={"document_id": str(doc.id), "question": "What is this?"}
    )
    assert response.status_code == 400
    assert "not ready" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ask_question_not_found(client: AsyncClient):
    """Test asking question on non-existent document returns 404."""
    response = await client.post(
        "/api/v1/chat/ask",
        json={
            "document_id": "00000000-0000-0000-0000-000000000000",
            "question"   : "What is this?"
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ask_question_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful Q&A with mocked Gemini."""
    doc_id = await create_completed_document(db_session)

    mock_result = {
        "answer"    : "This document is about Python programming.",
        "confidence": 0.95,
        "excerpt"   : "Python programming and FastAPI development."
    }

    with patch("app.api.routes.chat.GeminiService.answer_question", return_value=mock_result):
        response = await client.post(
            "/api/v1/chat/ask",
            json={"document_id": doc_id, "question": "What is this about?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This document is about Python programming."
    assert data["confidence"] == 0.95
    assert "session_id" in data


@pytest.mark.asyncio
async def test_ask_question_continues_session(client: AsyncClient, db_session: AsyncSession):
    """Test that session_id continues the same chat session."""
    doc_id = await create_completed_document(db_session)

    mock_result = {"answer": "Answer 1", "confidence": 0.9, "excerpt": ""}

    with patch("app.api.routes.chat.GeminiService.answer_question", return_value=mock_result):
        res1 = await client.post(
            "/api/v1/chat/ask",
            json={"document_id": doc_id, "question": "First question?"}
        )
    session_id = res1.json()["session_id"]

    mock_result2 = {"answer": "Answer 2", "confidence": 0.9, "excerpt": ""}
    with patch("app.api.routes.chat.GeminiService.answer_question", return_value=mock_result2):
        res2 = await client.post(
            "/api/v1/chat/ask",
            json={
                "document_id": doc_id,
                "question"   : "Second question?",
                "session_id" : session_id
            }
        )

    assert res2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_summarize_document(client: AsyncClient, db_session: AsyncSession):
    """Test document summarization with mocked Gemini."""
    doc_id = await create_completed_document(db_session)

    mock_summary = {
        "summary"            : "This is a test summary.",
        "key_points"         : ["Point 1", "Point 2"],
        "topics"             : ["Python", "FastAPI"],
        "word_count_estimate": 100
    }

    with patch("app.api.routes.chat.GeminiService.summarize", return_value=mock_summary):
        response = await client.post(
            "/api/v1/chat/summarize",
            json={"document_id": doc_id}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["cached"] == False
    assert data["summary_data"]["summary"] == "This is a test summary."
    assert len(data["summary_data"]["key_points"]) == 2


@pytest.mark.asyncio
async def test_summarize_returns_cached(client: AsyncClient, db_session: AsyncSession):
    """Test that second summarize call returns cached result."""
    doc_id = await create_completed_document(db_session)

    mock_summary = {
        "summary"            : "Cached summary.",
        "key_points"         : [],
        "topics"             : [],
        "word_count_estimate": 50
    }

    # First call — generates summary
    with patch("app.api.routes.chat.GeminiService.summarize", return_value=mock_summary):
        await client.post("/api/v1/chat/summarize", json={"document_id": doc_id})

    # Second call — should return cached
    response = await client.post(
        "/api/v1/chat/summarize",
        json={"document_id": doc_id}
    )
    assert response.status_code == 200
    assert response.json()["cached"] == True


@pytest.mark.asyncio
async def test_get_chat_history(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving chat history for a document."""
    doc_id = await create_completed_document(db_session)

    mock_result = {"answer": "Test answer", "confidence": 0.9, "excerpt": ""}
    with patch("app.api.routes.chat.GeminiService.answer_question", return_value=mock_result):
        await client.post(
            "/api/v1/chat/ask",
            json={"document_id": doc_id, "question": "Test question?"}
        )

    response = await client.get(f"/api/v1/chat/sessions/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 1
    assert len(data["sessions"][0]["messages"]) == 2
    assert data["sessions"][0]["messages"][0]["role"] == "user"
    assert data["sessions"][0]["messages"][1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_get_chat_history_invalid_id(client: AsyncClient):
    """Test chat history with invalid document ID."""
    response = await client.get("/api/v1/chat/sessions/not-a-uuid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_all_sessions(client: AsyncClient, db_session: AsyncSession):
    """Test getting all sessions."""
    response = await client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_ask_question_invalid_id(client: AsyncClient):
    """Test ask question with invalid document ID."""
    response = await client.post(
        "/api/v1/chat/ask",
        json={"document_id": "not-a-uuid", "question": "test?"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_summarize_invalid_id(client: AsyncClient):
    """Test summarize with invalid document ID."""
    response = await client.post(
        "/api/v1/chat/summarize",
        json={"document_id": "not-a-uuid"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_summarize_not_found(client: AsyncClient):
    """Test summarize non-existent document."""
    response = await client.post(
        "/api/v1/chat/summarize",
        json={"document_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ask_question_no_extracted_text(client: AsyncClient, db_session: AsyncSession):
    """Test asking question on document with no extracted text."""
    from app.models.document import Document, FileType, ProcessingStatus
    doc = Document(
        filename      = "empty.pdf",
        original_name = "empty.pdf",
        file_type     = FileType.PDF,
        file_size     = 100,
        file_path     = "/fake/empty.pdf",
        extracted_text= None,
        status        = ProcessingStatus.COMPLETED
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    response = await client.post(
        "/api/v1/chat/ask",
        json={"document_id": str(doc.id), "question": "What is this?"}
    )
    assert response.status_code == 400
    assert "No text" in response.json()["detail"]    

@pytest.mark.asyncio
async def test_ask_question_audio_document(client: AsyncClient, db_session: AsyncSession):
    """Test Q&A on audio document with transcript."""
    import json
    import tempfile
    import os

    # Create temp transcript file
    transcript = {
        "text": "Hello world audio content",
        "segments": [{"start": 0.0, "end": 5.0, "text": "Hello world"}],
        "language": "en",
        "duration": 5.0
    }
    with tempfile.NamedTemporaryFile(suffix='_transcript.json', delete=False, mode='w') as f:
        json.dump(transcript, f)
        transcript_path = f.name

    try:
        doc = Document(
            filename        = "test.mp3",
            original_name   = "test.mp3",
            file_type       = FileType.AUDIO,
            file_size       = 1000,
            file_path       = "/fake/test.mp3",
            extracted_text  = "Hello world audio content",
            transcript_path = transcript_path,
            duration        = 5.0,
            status          = ProcessingStatus.COMPLETED
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        mock_result = {
            "answer"           : "The audio discusses hello world.",
            "relevant_segments": [{"start": 0.0, "end": 5.0, "text": "Hello world",
                                   "relevance": "matches", "timestamp_formatted": "00:00:00"}]
        }

        with patch("app.api.routes.chat.GeminiService.find_topics_with_timestamps",
                   return_value=mock_result):
            response = await client.post(
                "/api/v1/chat/ask",
                json={"document_id": str(doc.id), "question": "What is discussed?"}
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["timestamps"]) > 0

    finally:
        os.unlink(transcript_path)


@pytest.mark.asyncio
async def test_ask_question_audio_no_transcript(client: AsyncClient, db_session: AsyncSession):
    """Test Q&A on audio document without transcript file falls back."""
    doc = Document(
        filename       = "test.mp3",
        original_name  = "test.mp3",
        file_type      = FileType.AUDIO,
        file_size      = 1000,
        file_path      = "/fake/test.mp3",
        extracted_text = "Hello world audio content",
        transcript_path= "/nonexistent/transcript.json",
        status         = ProcessingStatus.COMPLETED
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    mock_result = {"answer": "Fallback answer", "confidence": 0.8, "excerpt": ""}
    with patch("app.api.routes.chat.GeminiService.answer_question", return_value=mock_result):
        response = await client.post(
            "/api/v1/chat/ask",
            json={"document_id": str(doc.id), "question": "What is this?"}
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ask_question_video_document(client: AsyncClient, db_session: AsyncSession):
    """Test Q&A on video document."""
    import json, tempfile, os

    transcript = {
        "text": "Video content here",
        "segments": [{"start": 0.0, "end": 10.0, "text": "Video content"}],
        "language": "en",
        "duration": 10.0
    }
    with tempfile.NamedTemporaryFile(suffix='_transcript.json', delete=False, mode='w') as f:
        json.dump(transcript, f)
        transcript_path = f.name

    try:
        doc = Document(
            filename        = "test.mp4",
            original_name   = "test.mp4",
            file_type       = FileType.VIDEO,
            file_size       = 5000,
            file_path       = "/fake/test.mp4",
            extracted_text  = "Video content here",
            transcript_path = transcript_path,
            duration        = 10.0,
            status          = ProcessingStatus.COMPLETED
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        mock_result = {
            "answer"           : "Video answer",
            "relevant_segments": []
        }
        with patch("app.api.routes.chat.GeminiService.find_topics_with_timestamps",
                   return_value=mock_result):
            response = await client.post(
                "/api/v1/chat/ask",
                json={"document_id": str(doc.id), "question": "What is in the video?"}
            )

        assert response.status_code == 200

    finally:
        os.unlink(transcript_path)    