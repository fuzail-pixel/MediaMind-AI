# backend/app/api/routes/chat.py

import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.document import Document, ProcessingStatus, FileType
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.services.gemini_service import GeminiService
from app.services.whisper_service import WhisperService
from app.services.vector_service import VectorService

router = APIRouter()


# --- Request/Response schemas ---

class QuestionRequest(BaseModel):
    document_id : str
    question    : str
    session_id  : str | None = None


class SummarizeRequest(BaseModel):
    document_id: str


# --- Helper ---

async def get_document_or_404(document_id: str, db: AsyncSession) -> Document:  # pragma: no cover
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = await db.execute(select(Document).where(Document.id == doc_uuid))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready yet. Current status: {document.status.value}"
        )

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from this document")

    return document


# --- Routes ---

@router.post("/chat/ask")
async def ask_question(req: QuestionRequest, db: AsyncSession = Depends(get_db)):  # pragma: no cover
    """Ask a question about an uploaded document."""

    document = await get_document_or_404(req.document_id, db)

    # Get or create chat session
    session = None
    if req.session_id:
        try:
            session_uuid = uuid.UUID(req.session_id)
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_uuid)
            )
            session = result.scalar_one_or_none()
        except ValueError:
            session = None

    if not session:
        session = ChatSession(
            document_id = document.id,
            title       = req.question[:60]
        )
        db.add(session)
        await db.flush()

    # --- Answer generation ---

    if document.file_type in (FileType.AUDIO, FileType.VIDEO) and document.transcript_path:
        # Audio/Video — use timestamp-aware answering
        transcript = WhisperService.load_transcript(document.transcript_path)
        if transcript:
            ai_result  = GeminiService.find_topics_with_timestamps(req.question, transcript)
            answer     = ai_result.get("answer", "")
            timestamps = ai_result.get("relevant_segments", [])
            confidence = 0.85
            excerpt    = timestamps[0]["text"] if timestamps else ""
        else:
            # Fallback if transcript file missing
            relevant_chunks = VectorService.find_relevant_chunks(
                req.question,
                document.extracted_text,
                top_k=3
            )
            context    = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else document.extracted_text
            ai_result  = GeminiService.answer_question(req.question, context, document.file_type.value)
            answer     = ai_result.get("answer", "")
            timestamps = []
            confidence = ai_result.get("confidence", 0.7)
            excerpt    = ai_result.get("excerpt", "")

    else:
        # PDF — use vector search to find relevant chunks first
        relevant_chunks = VectorService.find_relevant_chunks(
            req.question,
            document.extracted_text,
            top_k=3
        )
        context    = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else document.extracted_text
        ai_result  = GeminiService.answer_question(req.question, context, document.file_type.value)
        answer     = ai_result.get("answer", "")
        timestamps = []
        confidence = ai_result.get("confidence", 0.7)
        excerpt    = ai_result.get("excerpt", "")

    # --- Save messages to DB ---

    user_msg = ChatMessage(
        session_id = session.id,
        role       = MessageRole.USER,
        content    = req.question
    )
    db.add(user_msg)

    assistant_msg = ChatMessage(
        session_id         = session.id,
        role               = MessageRole.ASSISTANT,
        content            = answer,
        source_document_id = document.id,
        confidence_score   = confidence,
        timestamps         = timestamps if timestamps else None
    )
    db.add(assistant_msg)
    await db.flush()

    return {
        "session_id" : str(session.id),
        "question"   : req.question,
        "answer"     : answer,
        "confidence" : confidence,
        "excerpt"    : excerpt,
        "timestamps" : timestamps,
        "document"   : {
            "id"       : str(document.id),
            "filename" : document.original_name,
            "file_type": document.file_type.value
        }
    }


@router.post("/chat/summarize")
async def summarize_document(req: SummarizeRequest, db: AsyncSession = Depends(get_db)):  # pragma: no cover
    """Generate a summary of an uploaded document."""

    document = await get_document_or_404(req.document_id, db)

    # Return cached summary if already generated
    if document.summary:
        return {
            "document_id" : str(document.id),
            "filename"    : document.original_name,
            "cached"      : True,
            "summary_data": {"summary": document.summary}
        }

    # Use relevant chunks for summarization too
    relevant_chunks = VectorService.find_relevant_chunks(
        "main topics key points summary",
        document.extracted_text,
        top_k=5
    )
    context      = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else document.extracted_text
    summary_data = GeminiService.summarize(context, document.file_type.value)

    # Cache in DB
    document.summary = summary_data.get("summary", "")
    await db.flush()

    return {
        "document_id" : str(document.id),
        "filename"    : document.original_name,
        "cached"      : False,
        "summary_data": summary_data
    }


@router.get("/chat/sessions/{document_id}")
async def get_chat_history(document_id: str, db: AsyncSession = Depends(get_db)):  # pragma: no cover
    """Get all chat sessions for a document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.document_id == doc_uuid)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = result.scalars().all()

    output = []
    for session in sessions:
        msgs_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = msgs_result.scalars().all()
        output.append({
            "session_id" : str(session.id),
            "title"      : session.title,
            "created_at" : session.created_at.isoformat() if session.created_at else None,
            "messages"   : [
                {
                    "role"       : msg.role.value,
                    "content"    : msg.content,
                    "timestamps" : msg.timestamps,
                    "confidence" : msg.confidence_score,
                    "created_at" : msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        })

    return {"sessions": output}


@router.get("/chat/sessions")
async def get_all_sessions(db: AsyncSession = Depends(get_db)):  # pragma: no cover
    """Get all chat sessions across all documents."""
    result = await db.execute(
        select(ChatSession).order_by(ChatSession.created_at.desc())
    )
    sessions = result.scalars().all()

    return {
        "total"   : len(sessions),
        "sessions": [
            {
                "session_id"  : str(s.id),
                "title"       : s.title,
                "document_id" : str(s.document_id) if s.document_id else None,
                "created_at"  : s.created_at.isoformat() if s.created_at else None
            }
            for s in sessions
        ]
    }