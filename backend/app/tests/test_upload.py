# backend/app/tests/test_upload.py

import pytest
import io
import os
import uuid
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy import select
from app.models.document import Document, FileType, ProcessingStatus


# Mock process_document for ALL tests in this file
# This prevents background task from hitting real PostgreSQL during tests
@pytest.fixture(autouse=True)
def mock_process_document():
    with patch("app.api.routes.upload.process_document", new_callable=AsyncMock):
        yield


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "MediaMind AI"


@pytest.mark.asyncio
async def test_upload_pdf(client: AsyncClient):
    pdf_content = b"%PDF-1.4 fake pdf content for testing purposes only"
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "pdf"
    assert data["status"] == "pending"
    assert "document_id" in data
    assert data["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_upload_audio(client: AsyncClient):
    audio_content = b"fake audio content"
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "audio"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_video(client: AsyncClient):
    video_content = b"fake video content"
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == "video"


@pytest.mark.asyncio
async def test_upload_unsupported_type(client: AsyncClient):
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", io.BytesIO(b"text"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_too_large(client: AsyncClient):
    large_content = b"x" * (51 * 1024 * 1024)
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient):
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["documents"] == []


@pytest.mark.asyncio
async def test_list_documents_after_upload(client: AsyncClient):
    pdf_content = b"%PDF-1.4 test content"
    await client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_get_document(client: AsyncClient):
    pdf_content = b"%PDF-1.4 test"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    response = await client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/documents/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_document_invalid_id(client: AsyncClient):
    response = await client.get("/api/v1/documents/not-a-uuid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient):
    pdf_content = b"%PDF-1.4 test"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    delete_res = await client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_res.status_code == 200
    assert "deleted successfully" in delete_res.json()["message"]

    get_res = await client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_search_short_query(client: AsyncClient):
    response = await client.get("/api/v1/search?q=ab")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_valid_query(client: AsyncClient):
    """Test search with valid query returns results structure."""
    with patch("app.api.routes.upload.VectorService.search_similar", 
               new_callable=AsyncMock,
               return_value=[]):
        response = await client.get("/api/v1/search?q=Junior Engineer")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert data["query"] == "Junior Engineer"


@pytest.mark.asyncio
async def test_delete_document_not_found(client: AsyncClient):
    """Test deleting non-existent document returns 404."""
    response = await client.delete("/api/v1/documents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_invalid_id(client: AsyncClient):
    """Test deleting with invalid ID returns 400."""
    response = await client.delete("/api/v1/documents/not-a-uuid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_wav(client: AsyncClient):
    """Test uploading WAV audio file."""
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.wav", io.BytesIO(b"fake wav"), "audio/wav")}
    )
    assert response.status_code == 201
    assert response.json()["file_type"] == "audio"


@pytest.mark.asyncio
async def test_upload_avi(client: AsyncClient):
    """Test uploading AVI video file."""
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.avi", io.BytesIO(b"fake avi"), "video/avi")}
    )
    assert response.status_code == 201
    assert response.json()["file_type"] == "video"


@pytest.mark.asyncio
async def test_serve_file_success(client: AsyncClient):
    pdf_content = b"%PDF-1.4 test"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    response = await client.get(f"/api/v1/documents/{doc_id}/file")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content == pdf_content


@pytest.mark.asyncio
async def test_serve_file_not_found(client: AsyncClient):
    response = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000/file")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_serve_file_invalid_id(client: AsyncClient):
    response = await client.get("/api/v1/documents/not-a-uuid/file")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_document_truncates_extracted_text(client: AsyncClient, db_session):
    pdf_content = b"%PDF-1.4 test"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("long.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    doc = result.scalar_one()
    doc.extracted_text = "x" * 900
    await db_session.commit()

    response = await client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["extracted_text"]) == 500


@pytest.mark.asyncio
async def test_delete_document_removes_transcript_file(client: AsyncClient, db_session):
    audio_content = b"fake audio"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("audio.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    )
    doc_id = upload_res.json()["document_id"]

    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    doc = result.scalar_one()

    transcript_path = doc.file_path + "_transcript.json"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write('{"text":"hello"}')

    doc.transcript_path = transcript_path
    await db_session.commit()

    assert os.path.exists(transcript_path)

    delete_res = await client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_res.status_code == 200
    assert not os.path.exists(transcript_path)


@pytest.mark.asyncio
async def test_serve_file_missing_on_disk(client: AsyncClient, db_session):
    pdf_content = b"%PDF-1.4 test"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("gone.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    doc_id = upload_res.json()["document_id"]

    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    doc = result.scalar_one()

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    response = await client.get(f"/api/v1/documents/{doc_id}/file")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found on disk"


@pytest.mark.asyncio
async def test_serve_file_mime_fallback_audio(client: AsyncClient):
    audio_content = b"fake audio"
    upload_res = await client.post(
        "/api/v1/upload",
        files={"file": ("fallback.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    )
    doc_id = upload_res.json()["document_id"]

    with patch("app.api.routes.upload.mimetypes.guess_type", return_value=(None, None)):
        response = await client.get(f"/api/v1/documents/{doc_id}/file")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")


@pytest.mark.asyncio
async def test_serve_file_not_found_uuid(client: AsyncClient):
    """Test serving non-existent document returns 404."""
    response = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000001/serve")
    assert response.status_code == 404


@pytest.mark.asyncio  
async def test_upload_mkv(client: AsyncClient):
    """Test uploading MKV video file."""
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.mkv", io.BytesIO(b"fake mkv"), "video/mkv")}
    )
    assert response.status_code == 201
    assert response.json()["file_type"] == "video"


@pytest.mark.asyncio
async def test_upload_m4a(client: AsyncClient):
    """Test uploading M4A audio file."""
    response = await client.post(
        "/api/v1/upload",
        files={"file": ("test.m4a", io.BytesIO(b"fake m4a"), "audio/m4a")}
    )
    assert response.status_code == 201
    assert response.json()["file_type"] == "audio"    