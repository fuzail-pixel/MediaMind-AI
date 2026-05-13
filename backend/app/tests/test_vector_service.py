# backend/app/tests/test_vector_service.py

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.vector_service import VectorService


def test_chunk_text_basic():
    """Test text chunking splits correctly."""
    text = "A" * 600
    chunks = VectorService.chunk_text(text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= VectorService.CHUNK_SIZE + 10


def test_chunk_text_short():
    """Test short text returns single chunk."""
    text = "Short text"
    chunks = VectorService.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "Short text"


def test_chunk_text_empty():
    """Test empty text returns empty list."""
    chunks = VectorService.chunk_text("")
    assert chunks == []


def test_chunk_text_sentence_boundary():
    """Test chunking respects sentence boundaries."""
    text = ("Hello world. " * 40) + ("Goodbye world. " * 40)
    chunks = VectorService.chunk_text(text)
    assert len(chunks) > 1


def test_embed_text():
    """Test embedding returns correct dimensions."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * 384)

    with patch.object(VectorService, 'get_model', return_value=mock_model):
        result = VectorService.embed_text("test text")

    assert isinstance(result, list)
    assert len(result) == 384


def test_find_relevant_chunks_empty_text():
    """Test relevant chunks with empty text."""
    result = VectorService.find_relevant_chunks("query", "", top_k=3)
    assert result == []


def test_find_relevant_chunks_success():
    """Test finding relevant chunks returns top_k results."""
    mock_model = MagicMock()
    mock_model.encode.side_effect = [
        np.array([1.0, 0.0, 0.0]),   # query embedding
        np.array([[1.0, 0.0, 0.0],   # chunk 1 — most similar
                  [0.0, 1.0, 0.0],   # chunk 2
                  [0.0, 0.0, 1.0]])  # chunk 3
    ]

    text = "First chunk content. " * 30 + "Second chunk content. " * 30 + "Third chunk content. " * 30

    with patch.object(VectorService, 'get_model', return_value=mock_model):
        results = VectorService.find_relevant_chunks("query", text, top_k=2)

    assert len(results) <= 2
    assert all(isinstance(c, str) for c in results)


def test_find_relevant_chunks_top_k():
    """Test top_k limits results correctly."""
    mock_model = MagicMock()
    embeddings = np.random.rand(5, 10)
    mock_model.encode.side_effect = [
        np.random.rand(10),
        embeddings
    ]

    text = ("chunk content here. " * 30) * 5

    with patch.object(VectorService, 'get_model', return_value=mock_model):
        results = VectorService.find_relevant_chunks("query", text, top_k=3)

    assert len(results) <= 3


@pytest.mark.asyncio
async def test_store_embeddings_no_text():
    """Test store_embeddings returns False with no text."""
    from unittest.mock import MagicMock
    mock_doc = MagicMock()
    mock_doc.extracted_text = None
    mock_db = AsyncMock()

    result = await VectorService.store_embeddings(mock_db, mock_doc)
    assert result == False


@pytest.mark.asyncio
async def test_store_embeddings_success():
    """Test store_embeddings succeeds with valid text."""
    mock_doc = MagicMock()
    mock_doc.extracted_text = "This is test document content for embedding."
    mock_doc.id = "test-uuid-123"

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()

    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * 384)

    with patch.object(VectorService, 'get_model', return_value=mock_model):
        result = await VectorService.store_embeddings(mock_db, mock_doc)

    assert result == True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_search_similar_success():
    """Test vector search returns results."""
    mock_db = AsyncMock()

    mock_row = MagicMock()
    mock_row.id = "test-uuid"
    mock_row.original_name = "test.pdf"
    mock_row.file_type = "pdf"
    mock_row.extracted_text = "Test content"
    mock_row.similarity = 0.85

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * 384)

    with patch.object(VectorService, 'get_model', return_value=mock_model):
        results = await VectorService.search_similar(mock_db, "test query", limit=5)

    assert len(results) == 1
    assert results[0]["filename"] == "test.pdf"
    assert results[0]["similarity"] == 0.85


@pytest.mark.asyncio
async def test_search_similar_error():
    """Test vector search handles errors gracefully."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("DB error"))

    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * 384)

    with patch.object(VectorService, 'get_model', return_value=mock_model):
        results = await VectorService.search_similar(mock_db, "test query")

    assert results == []