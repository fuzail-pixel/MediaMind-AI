# backend/app/services/gemini_service.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from app.core.config import get_settings
from typing import Optional
import json

settings = get_settings()


class GeminiService:
    _llm: Optional[ChatGoogleGenerativeAI] = None

    @classmethod
    def get_llm(cls) -> ChatGoogleGenerativeAI:
        """Lazy load — only initializes on first use."""
        if cls._llm is None:
            cls._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
                max_tokens=2048,
                max_retries=1,
                timeout=30
            )
            print("✅ Gemini model loaded")
        return cls._llm


    @classmethod
    def answer_question(cls, question: str, context: str, file_type: str = "document") -> dict:
        """
        Answer a question based on the extracted text/transcript context.
        Returns answer + confidence + relevant excerpt.
        """
        llm = cls.get_llm()

        prompt = f"""You are an intelligent assistant that answers questions based ONLY on the provided content.

Content Type: {file_type}

Content:
\"\"\"
{context[:8000]}
\"\"\"

Question: {question}

Instructions:
- Answer based strictly on the content above
- If the answer is not in the content, say "I couldn't find this information in the provided content"
- Be concise and precise
- If this is a transcript, mention approximate timestamps if relevant

Respond in this exact JSON format:
{{
    "answer": "your detailed answer here",
    "confidence": 0.95,
    "excerpt": "the most relevant excerpt from the content that supports your answer"
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])

        try:
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception:
            return {
                "answer"    : response.content,
                "confidence": 0.7,
                "excerpt"   : ""
            }


    @classmethod
    def summarize(cls, text: str, file_type: str = "document") -> dict:
        """
        Generate a structured summary of the document/transcript.
        """
        llm = cls.get_llm()

        type_instruction = {
            "pdf"   : "This is a PDF document. Provide a professional summary.",
            "audio" : "This is an audio transcript. Summarize the key discussion points.",
            "video" : "This is a video transcript. Summarize the main topics covered."
        }.get(file_type, "Provide a clear summary.")

        prompt = f"""You are a summarization expert. {type_instruction}

Content:
\"\"\"
{text[:8000]}
\"\"\"

Respond in this exact JSON format:
{{
    "summary": "2-3 paragraph summary of the main content",
    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
    "topics": ["topic1", "topic2", "topic3"],
    "word_count_estimate": 500
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])

        try:
            text_response = response.content.strip()
            if text_response.startswith("```"):
                text_response = text_response.split("```")[1]
                if text_response.startswith("json"):
                    text_response = text_response[4:]
            return json.loads(text_response.strip())
        except Exception:
            return {
                "summary"            : response.content,
                "key_points"         : [],
                "topics"             : [],
                "word_count_estimate": 0
            }


    @classmethod
    def find_topics_with_timestamps(cls, question: str, transcript_data: dict) -> dict:
        """
        For audio/video — find which timestamps are relevant to a question.
        """
        segments = transcript_data.get("segments", [])

        # Check BEFORE loading LLM — avoids credential errors in CI
        if not segments:
            return {"timestamps": [], "answer": "No transcript segments available"}

        llm = cls.get_llm()

        segment_list = "\n".join([
            f"[{s['start']}s - {s['end']}s]: {s['text']}"
            for s in segments[:100]
        ])

        prompt = f"""Given these transcript segments with timestamps, find the ones most relevant to the question.

Question: {question}

Transcript Segments:
{segment_list}

Respond in this exact JSON format:
{{
    "answer": "direct answer to the question",
    "relevant_segments": [
        {{"start": 12.5, "end": 24.0, "text": "segment text", "relevance": "why this is relevant"}}
    ]
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])

        try:
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text.strip())

            for seg in result.get("relevant_segments", []):
                seg["timestamp_formatted"] = GeminiService._format_timestamp(seg["start"])

            return result
        except Exception:
            return {
                "answer"           : response.content,
                "relevant_segments": []
            }


    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"