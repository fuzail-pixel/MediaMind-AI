# backend/app/services/whisper_service.py

import os
import json
from typing import Optional
from faster_whisper import WhisperModel


class WhisperService:
    # Class-level model — loaded once, reused for all requests
    _model: Optional[WhisperModel] = None
    MODEL_SIZE = "base"   # tiny/base/small/medium — base is best free balance

    @classmethod
    def get_model(cls) -> WhisperModel:
        """Lazy load the model — only loads when first transcription happens."""
        if cls._model is None:
            print("⏳ Loading Whisper model (first time only, may take a moment)...")
            cls._model = WhisperModel(
                cls.MODEL_SIZE,
                device="cpu",           # use CPU (free, no GPU needed)
                compute_type="int8"     # int8 = faster on CPU, less memory
            )
            print("✅ Whisper model loaded successfully")
        return cls._model


    @classmethod
    def transcribe(cls, file_path: str) -> dict:
        """
        Transcribe an audio or video file.
        Returns full transcript text + timestamped segments.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        model = cls.get_model()

        print(f"🎙️ Transcribing: {file_path}")

        segments, info = model.transcribe(
            file_path,
            beam_size=5,
            word_timestamps=True,      # enables word-level timestamps
            vad_filter=True,           # skip silent parts automatically
        )

        # Build structured output
        full_text = []
        structured_segments = []

        for segment in segments:
            full_text.append(segment.text.strip())
            structured_segments.append({
                "start"     : round(segment.start, 2),
                "end"       : round(segment.end, 2),
                "text"      : segment.text.strip(),
                "words"     : [
                    {
                        "word"  : w.word.strip(),
                        "start" : round(w.start, 2),
                        "end"   : round(w.end, 2)
                    }
                    for w in (segment.words or [])
                ]
            })

        return {
            "text"      : " ".join(full_text),
            "segments"  : structured_segments,
            "language"  : info.language,
            "duration"  : round(info.duration, 2)
        }


    @staticmethod
    def save_transcript(transcript: dict, output_path: str) -> str:
        """Save full transcript with timestamps to a JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
        return output_path


    @staticmethod
    def load_transcript(transcript_path: str) -> Optional[dict]:
        """Load a saved transcript JSON file."""
        if not os.path.exists(transcript_path):
            return None
        with open(transcript_path, "r", encoding="utf-8") as f:
            return json.load(f)


    @classmethod
    def find_timestamp_for_topic(cls,transcript: dict, topic: str) -> list:
        """
        Search transcript segments for a topic/keyword.
        Returns list of matching segments with timestamps.
        """
        topic_lower = topic.lower()
        matches = []

        for segment in transcript.get("segments", []):
            if topic_lower in segment["text"].lower():
                matches.append({
                    "start"     : segment["start"],
                    "end"       : segment["end"],
                    "text"      : segment["text"],
                    "timestamp" : cls._format_timestamp(segment["start"])
                })

        return matches


    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"