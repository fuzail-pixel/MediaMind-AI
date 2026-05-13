# backend/app/tests/test_whisper_service.py

import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from app.services.whisper_service import WhisperService


def test_format_timestamp():
    """Test timestamp formatting."""
    assert WhisperService._format_timestamp(0)    == "00:00:00"
    assert WhisperService._format_timestamp(61)   == "00:01:01"
    assert WhisperService._format_timestamp(3600) == "01:00:00"


def test_save_and_load_transcript(tmp_path):
    """Test saving and loading transcript JSON."""
    transcript = {
        "text"    : "Hello world",
        "segments": [{"start": 0.0, "end": 2.0, "text": "Hello world"}],
        "language": "en",
        "duration": 2.0
    }
    path = str(tmp_path / "test_transcript.json")
    WhisperService.save_transcript(transcript, path)

    assert os.path.exists(path)

    loaded = WhisperService.load_transcript(path)
    assert loaded["text"]     == "Hello world"
    assert loaded["duration"] == 2.0
    assert len(loaded["segments"]) == 1


def test_load_transcript_missing_file():
    """Test loading non-existent transcript returns None."""
    result = WhisperService.load_transcript("/nonexistent/transcript.json")
    assert result is None


def test_find_timestamp_for_topic():
    """Test finding timestamps for a topic."""
    transcript = {
        "segments": [
            {"start": 0.0,  "end": 5.0,  "text": "Welcome to the presentation"},
            {"start": 5.0,  "end": 10.0, "text": "Today we discuss Python programming"},
            {"start": 10.0, "end": 15.0, "text": "FastAPI is a modern web framework"},
        ]
    }

    results = WhisperService.find_timestamp_for_topic(transcript, "Python")
    assert len(results) == 1
    assert results[0]["start"] == 5.0
    assert "Python" in results[0]["text"]


def test_find_timestamp_for_topic_no_match():
    """Test finding timestamps with no matching topic."""
    transcript = {
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "Hello world"}
        ]
    }
    results = WhisperService.find_timestamp_for_topic(transcript, "quantum physics")
    assert results == []


def test_transcribe_file_not_found():
    """Test transcription of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        WhisperService.transcribe("/nonexistent/audio.mp3")


def test_transcribe_success():
    """Test successful transcription with mocked Whisper model."""
    mock_segment      = MagicMock()
    mock_segment.text = " Hello world"
    mock_segment.start = 0.0
    mock_segment.end   = 2.0
    mock_segment.words = []

    mock_info          = MagicMock()
    mock_info.language = "en"
    mock_info.duration = 2.0

    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b"fake audio")
        path = f.name

    try:
        with patch.object(WhisperService, 'get_model') as mock_get_model:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([mock_segment], mock_info)
            mock_get_model.return_value = mock_model

            result = WhisperService.transcribe(path)

        assert result["text"]     == "Hello world"
        assert result["language"] == "en"
        assert result["duration"] == 2.0
        assert len(result["segments"]) == 1
    finally:
        os.unlink(path)