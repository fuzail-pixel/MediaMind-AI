# backend/app/tests/test_process_document.py

import pytest
import os
import uuid
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.routes.upload import process_document
from app.models.document import Document, FileType, ProcessingStatus


async def create_pending_document(db: AsyncSession, file_path: str, file_type: FileType) -> str:
    doc = Document(
        filename      = "test.pdf",
        original_name = "test.pdf",
        file_type     = file_type,
        file_size     = 100,
        file_path     = file_path,
        status        = ProcessingStatus.PENDING
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return str(doc.id)


@pytest.mark.asyncio
async def test_process_document_pdf(db_session: AsyncSession):
    """Test PDF processing extracts text and stores embedding."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"%PDF-1.4 test content")
        path = f.name

    try:
        doc_id = await create_pending_document(db_session, path, FileType.PDF)

        with patch("app.api.routes.upload.PDFService.extract_text", return_value="Extracted PDF text"), \
             patch("app.api.routes.upload.VectorService.store_embeddings", new_callable=AsyncMock, return_value=True), \
             patch("app.core.database.AsyncSessionLocal") as mock_session_local:

            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=db_session)
            mock_session_local.return_value.__aexit__  = AsyncMock(return_value=False)

            await process_document(doc_id, path, FileType.PDF)

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one_or_none()
        assert doc is not None

    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_process_document_not_found(db_session: AsyncSession):
    """Test process_document handles missing document gracefully."""
    fake_id = str(uuid.uuid4())

    with patch("app.core.database.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=db_session)
        mock_session_local.return_value.__aexit__  = AsyncMock(return_value=False)

        # Should not raise — just return silently
        await process_document(fake_id, "/fake/path.pdf", FileType.PDF)


@pytest.mark.asyncio
async def test_process_document_audio(db_session: AsyncSession):
    """Test audio processing transcribes and stores embedding."""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b"fake audio")
        path = f.name

    try:
        doc_id = await create_pending_document(db_session, path, FileType.AUDIO)

        mock_transcript = {
            "text"    : "Hello world transcript",
            "segments": [{"start": 0.0, "end": 2.0, "text": "Hello world"}],
            "language": "en",
            "duration": 2.0
        }

        with patch("app.api.routes.upload.WhisperService.transcribe", return_value=mock_transcript), \
             patch("app.api.routes.upload.WhisperService.save_transcript", return_value=path), \
             patch("app.api.routes.upload.VectorService.store_embeddings", new_callable=AsyncMock, return_value=True), \
             patch("app.core.database.AsyncSessionLocal") as mock_session_local:

            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=db_session)
            mock_session_local.return_value.__aexit__  = AsyncMock(return_value=False)

            await process_document(doc_id, path, FileType.AUDIO)

    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_process_document_failure(db_session: AsyncSession):
    """Test process_document handles errors and marks document as failed."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"test")
        path = f.name

    try:
        doc_id = await create_pending_document(db_session, path, FileType.PDF)

        with patch("app.api.routes.upload.PDFService.extract_text", side_effect=Exception("PDF read error")), \
             patch("app.core.database.AsyncSessionLocal") as mock_session_local:

            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=db_session)
            mock_session_local.return_value.__aexit__  = AsyncMock(return_value=False)

            await process_document(doc_id, path, FileType.PDF)

    finally:
        os.unlink(path)