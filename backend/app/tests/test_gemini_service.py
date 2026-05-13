# backend/app/tests/test_gemini_service.py

import pytest
from unittest.mock import patch, MagicMock
from app.services.gemini_service import GeminiService


def test_format_timestamp_seconds():
    """Test timestamp formatting."""
    assert GeminiService._format_timestamp(0)    == "00:00:00"
    assert GeminiService._format_timestamp(65)   == "00:01:05"
    assert GeminiService._format_timestamp(3661) == "01:01:01"
    assert GeminiService._format_timestamp(90)   == "00:01:30"


def test_answer_question_success():
    """Test answer_question with mocked LLM."""
    mock_response = MagicMock()
    mock_response.content = '{"answer": "Test answer", "confidence": 0.9, "excerpt": "test"}'

    with patch.object(GeminiService, 'get_llm') as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.answer_question("What is this?", "Test context")

    assert result["answer"] == "Test answer"
    assert result["confidence"] == 0.9
    assert result["excerpt"] == "test"


def test_answer_question_json_with_fences():
    """Test JSON parsing strips markdown code fences."""
    mock_response = MagicMock()
    mock_response.content = '```json\n{"answer": "Fenced", "confidence": 0.8, "excerpt": ""}\n```'

    with patch.object(GeminiService, 'get_llm') as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.answer_question("Question?", "Context")

    assert result["answer"] == "Fenced"


def test_answer_question_fallback_on_invalid_json():
    """Test fallback when LLM returns invalid JSON."""
    mock_response = MagicMock()
    mock_response.content = "This is not JSON at all"

    with patch.object(GeminiService, 'get_llm') as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.answer_question("Question?", "Context")

    assert result["answer"] == "This is not JSON at all"
    assert result["confidence"] == 0.7


def test_summarize_success():
    """Test summarize with mocked LLM."""
    mock_response = MagicMock()
    mock_response.content = '''
    {
        "summary": "Test summary text.",
        "key_points": ["Point 1", "Point 2"],
        "topics": ["Topic 1"],
        "word_count_estimate": 100
    }
    '''

    with patch.object(GeminiService, 'get_llm') as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.summarize("Long document text here")

    assert result["summary"] == "Test summary text."
    assert len(result["key_points"]) == 2
    assert result["word_count_estimate"] == 100


def test_summarize_fallback():
    """Test summarize fallback on invalid JSON."""
    mock_response = MagicMock()
    mock_response.content = "Plain text summary"

    with patch.object(GeminiService, 'get_llm') as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.summarize("Some text")

    assert result["summary"] == "Plain text summary"
    assert result["key_points"] == []


def test_find_topics_with_timestamps_no_segments():
    """Test timestamp finding with empty transcript."""
    result = GeminiService.find_topics_with_timestamps(
        "question",
        {"segments": []}
    )
    assert result["timestamps"] == [] or "answer" in result


def test_find_topics_with_timestamps_success():
    """Test timestamp finding with mocked LLM."""
    mock_response = MagicMock()
    mock_response.content = '''
    {
        "answer": "Found at 12 seconds",
        "relevant_segments": [
            {"start": 12.0, "end": 24.0, "text": "relevant text", "relevance": "matches"}
        ]
    }
    '''
    transcript = {
        "segments": [
            {"start": 12.0, "end": 24.0, "text": "relevant text"}
        ]
    }

    with patch.object(GeminiService, 'get_llm') as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.find_topics_with_timestamps("question", transcript)

    assert result["answer"] == "Found at 12 seconds"
    assert result["relevant_segments"][0]["timestamp_formatted"] == "00:00:12"


def test_get_llm_lazy_initialization():
    original_llm = GeminiService._llm
    GeminiService._llm = None

    mock_instance = MagicMock()

    with patch("app.services.gemini_service.ChatGoogleGenerativeAI", return_value=mock_instance) as mock_ctor:
        llm1 = GeminiService.get_llm()
        llm2 = GeminiService.get_llm()

    assert llm1 is mock_instance
    assert llm2 is mock_instance
    mock_ctor.assert_called_once()

    GeminiService._llm = original_llm


def test_summarize_pdf_instruction_branch():
    mock_response = MagicMock()
    mock_response.content = '{"summary": "PDF summary", "key_points": [], "topics": [], "word_count_estimate": 10}'

    with patch.object(GeminiService, "get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.summarize("Some pdf text", file_type="pdf")

    assert result["summary"] == "PDF summary"


def test_summarize_audio_instruction_branch():
    mock_response = MagicMock()
    mock_response.content = '{"summary": "Audio summary", "key_points": [], "topics": [], "word_count_estimate": 10}'

    with patch.object(GeminiService, "get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.summarize("Some audio text", file_type="audio")

    assert result["summary"] == "Audio summary"


def test_summarize_video_instruction_branch():
    mock_response = MagicMock()
    mock_response.content = '{"summary": "Video summary", "key_points": [], "topics": [], "word_count_estimate": 10}'

    with patch.object(GeminiService, "get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.summarize("Some video text", file_type="video")

    assert result["summary"] == "Video summary"


def test_find_topics_with_timestamps_invalid_json_fallback():
    mock_response = MagicMock()
    mock_response.content = "not json"

    transcript = {
        "segments": [
            {"start": 12.0, "end": 24.0, "text": "relevant text"}
        ]
    }

    with patch.object(GeminiService, "get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        result = GeminiService.find_topics_with_timestamps("question", transcript)

    assert result["answer"] == "not json"
    assert result["relevant_segments"] == []