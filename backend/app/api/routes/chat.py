# backend/app/api/routes/chat.py

import json
from app.core.database import AsyncSessionLocal
import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.document import Document, ProcessingStatus, FileType
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.services.gemini_service import GeminiService
from app.services.whisper_service import WhisperService
from app.services.vector_service import VectorService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


# --- Request/Response schemas ---

class QuestionRequest(BaseModel):
    document_id: str
    question: str
    session_id: str | None = None


class SummarizeRequest(BaseModel):
    document_id: str


class StreamRequest(BaseModel):
    document_id: str
    question: str
    session_id: str | None = None


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
async def ask_question(
    req: QuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Ask a question about an uploaded document."""

    document = await get_document_or_404(req.document_id, db)

    session = None

    if req.session_id:
        try:
            session_uuid = uuid.UUID(req.session_id)

            result = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_uuid,
                    ChatSession.user_id == current_user.id
                )
            )

            session = result.scalar_one_or_none()

        except ValueError:
            session = None

    if not session:
        session = ChatSession(
            user_id=current_user.id,
            document_id=document.id,
            title=req.question[:60]
        )

        db.add(session)
        await db.flush()

    # --- Audio / Video handling ---
    if document.file_type in (FileType.AUDIO, FileType.VIDEO) and document.transcript_path:

        transcript = WhisperService.load_transcript(document.transcript_path)

        if transcript:
            ai_result = GeminiService.find_topics_with_timestamps(
                req.question,
                transcript
            )

            answer = ai_result.get("answer", "")
            timestamps = ai_result.get("relevant_segments", [])
            confidence = 0.85
            excerpt = timestamps[0]["text"] if timestamps else ""

        else:
            relevant_chunks = VectorService.find_relevant_chunks(
                req.question,
                document.extracted_text,
                top_k=3
            )

            context = (
                "\n\n---\n\n".join(relevant_chunks)
                if relevant_chunks
                else document.extracted_text
            )

            ai_result = GeminiService.answer_question(
                req.question,
                context,
                document.file_type.value
            )

            answer = ai_result.get("answer", "")
            timestamps = []
            confidence = ai_result.get("confidence", 0.7)
            excerpt = ai_result.get("excerpt", "")

    else:
        relevant_chunks = VectorService.find_relevant_chunks(
            req.question,
            document.extracted_text,
            top_k=3
        )

        context = (
            "\n\n---\n\n".join(relevant_chunks)
            if relevant_chunks
            else document.extracted_text
        )

        ai_result = GeminiService.answer_question(
            req.question,
            context,
            document.file_type.value
        )

        answer = ai_result.get("answer", "")
        timestamps = []
        confidence = ai_result.get("confidence", 0.7)
        excerpt = ai_result.get("excerpt", "")

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=req.question
    )

    db.add(user_msg)

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=answer,
        source_document_id=document.id,
        confidence_score=confidence,
        timestamps=timestamps if timestamps else None
    )

    db.add(assistant_msg)

    await db.flush()

    return {
        "session_id": str(session.id),
        "question": req.question,
        "answer": answer,
        "confidence": confidence,
        "excerpt": excerpt,
        "timestamps": timestamps,
        "document": {
            "id": str(document.id),
            "filename": document.original_name,
            "file_type": document.file_type.value
        }
    }


@router.post("/chat/summarize")
async def summarize_document(
    req: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Generate a summary of an uploaded document."""

    document = await get_document_or_404(req.document_id, db)

    if document.summary:
        return {
            "document_id": str(document.id),
            "filename": document.original_name,
            "cached": True,
            "summary_data": {
                "summary": document.summary
            }
        }

    relevant_chunks = VectorService.find_relevant_chunks(
        "main topics key points summary",
        document.extracted_text,
        top_k=5
    )

    context = (
        "\n\n---\n\n".join(relevant_chunks)
        if relevant_chunks
        else document.extracted_text
    )

    summary_data = GeminiService.summarize(
        context,
        document.file_type.value
    )

    document.summary = summary_data.get("summary", "")

    await db.flush()

    return {
        "document_id": str(document.id),
        "filename": document.original_name,
        "cached": False,
        "summary_data": summary_data
    }


@router.get("/chat/sessions/{document_id}")
async def get_chat_history(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Get all chat sessions for a document."""

    try:
        doc_uuid = uuid.UUID(document_id)

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.document_id == doc_uuid)
        .where(ChatSession.user_id == current_user.id)
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
            "session_id": str(session.id),
            "title": session.title,
            "created_at": (
                session.created_at.isoformat()
                if session.created_at
                else None
            ),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamps": msg.timestamps,
                    "confidence": msg.confidence_score,
                    "created_at": (
                        msg.created_at.isoformat()
                        if msg.created_at
                        else None
                    )
                }
                for msg in messages
            ]
        })

    return {
        "sessions": output
    }


@router.get("/chat/sessions")
async def get_all_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Get all chat sessions for current user."""

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )

    sessions = result.scalars().all()

    return {
        "total": len(sessions),
        "sessions": [
            {
                "session_id": str(s.id),
                "title": s.title,
                "document_id": (
                    str(s.document_id)
                    if s.document_id
                    else None
                ),
                "created_at": (
                    s.created_at.isoformat()
                    if s.created_at
                    else None
                )
            }
            for s in sessions
        ]
    }


@router.post("/chat/stream")
async def stream_answer(
    req: StreamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Stream AI answer word by word using Server-Sent Events."""

    document = await get_document_or_404(req.document_id, db)

    session = None

    if req.session_id:
        try:
            session_uuid = uuid.UUID(req.session_id)

            result = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_uuid,
                    ChatSession.user_id == current_user.id
                )
            )

            session = result.scalar_one_or_none()

        except ValueError:
            session = None

    if not session:
        session = ChatSession(
            user_id=current_user.id,
            document_id=document.id,
            title=req.question[:60]
        )

        db.add(session)
        await db.flush()

    session_id = str(session.id)

    relevant_chunks = VectorService.find_relevant_chunks(
        req.question,
        document.extracted_text,
        top_k=3
    )

    context = (
        "\n\n---\n\n".join(relevant_chunks)
        if relevant_chunks
        else document.extracted_text
    )

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=req.question
    )

    db.add(user_msg)
    await db.flush()

    async def generate():

        full_answer = []

        try:
            # Send session ID first
            yield (
                f"data: "
                f"{json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            )

            # Stream tokens
            async for token in GeminiService.stream_answer(
                req.question,
                context,
                document.file_type.value
            ):

                full_answer.append(token)

                yield (
                    f"data: "
                    f"{json.dumps({'type': 'token', 'content': token})}\n\n"
                )

            # Final complete answer
            complete_answer = "".join(full_answer)

            # Save assistant response
            async with AsyncSessionLocal() as save_db:

                assistant_msg = ChatMessage(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=complete_answer,
                    source_document_id=document.id,
                    confidence_score=0.85
                )

                save_db.add(assistant_msg)

                await save_db.commit()

            yield (
                f"data: "
                f"{json.dumps({'type': 'done', 'full_answer': complete_answer})}\n\n"
            )

        except Exception as e:

            yield (
                f"data: "
                f"{json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )