# backend/app/api/routes/upload.py

import os
import uuid
import aiofiles
import mimetypes
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import get_settings
from app.models.document import Document, FileType, ProcessingStatus
from app.models.user import User
from app.services.pdf_service import PDFService
from app.services.whisper_service import WhisperService
from app.services.vector_service import VectorService
from app.core.security import get_current_user

router = APIRouter()
settings = get_settings()

EXTENSION_MAP = {
    "pdf" : FileType.PDF,
    "mp3" : FileType.AUDIO,
    "wav" : FileType.AUDIO,
    "m4a" : FileType.AUDIO,
    "mp4" : FileType.VIDEO,
    "avi" : FileType.VIDEO,
    "mov" : FileType.VIDEO,
    "mkv" : FileType.VIDEO,
}


def get_file_type(filename: str) -> FileType:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in EXTENSION_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: pdf, mp3, wav, m4a, mp4, avi, mov, mkv"
        )
    return EXTENSION_MAP[ext]


async def process_document(document_id: str, file_path: str, file_type: FileType):
    """
    Background task — runs after upload returns response.
    Extracts text from PDF or transcribes audio/video, then stores embeddings.
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(document_id))
            )
            document = result.scalar_one_or_none()
            if not document:
                return

            document.status = ProcessingStatus.PROCESSING
            await db.commit()

            if file_type == FileType.PDF:
                extracted_text = PDFService.extract_text(file_path)
                document.extracted_text = extracted_text
                await db.commit()
                await VectorService.store_embeddings(db, document)
                document.status = ProcessingStatus.COMPLETED

            elif file_type in (FileType.AUDIO, FileType.VIDEO):
                transcript = WhisperService.transcribe(file_path)
                transcript_path = file_path.rsplit(".", 1)[0] + "_transcript.json"
                WhisperService.save_transcript(transcript, transcript_path)
                document.extracted_text  = transcript["text"]
                document.transcript_path = transcript_path
                document.duration        = transcript["duration"]
                await db.commit()
                await VectorService.store_embeddings(db, document)
                document.status = ProcessingStatus.COMPLETED

            await db.commit()
            print(f"✅ Document {document_id} processed successfully")

        except Exception as e:
            print(f"❌ Error processing document {document_id}: {e}")
            async with AsyncSessionLocal() as db2:
                result = await db2.execute(
                    select(Document).where(Document.id == uuid.UUID(document_id))
                )
                document = result.scalar_one_or_none()
                if document:
                    document.status        = ProcessingStatus.FAILED
                    document.error_message = str(e)
                    await db2.commit()


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Upload a PDF, audio, or video file for processing."""

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    contents  = await file.read()

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    file_type       = get_file_type(file.filename)
    ext             = file.filename.rsplit(".", 1)[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path       = os.path.join(settings.UPLOAD_DIR, unique_filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    document = Document(
        user_id       = current_user.id,
        filename      = unique_filename,
        original_name = file.filename,
        file_type     = file_type,
        file_size     = len(contents),
        file_path     = file_path,
        status        = ProcessingStatus.PENDING
    )
    db.add(document)
    await db.flush()

    doc_id = str(document.id)
    background_tasks.add_task(process_document, doc_id, file_path, file_type)

    return JSONResponse(
        status_code=201,
        content={
            "message"      : "File uploaded. Processing started in background.",
            "document_id"  : doc_id,
            "filename"     : document.original_name,
            "file_type"    : file_type.value,
            "file_size_kb" : round(len(contents) / 1024, 2),
            "status"       : ProcessingStatus.PENDING.value
        }
    )


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """List all uploaded documents for current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return {
        "total": len(documents),
        "documents": [
            {
                "id"          : str(doc.id),
                "filename"    : doc.original_name,
                "file_type"   : doc.file_type.value,
                "file_size_kb": round(doc.file_size / 1024, 2),
                "status"      : doc.status.value,
                "created_at"  : doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in documents
        ]
    }


@router.get("/search")
async def search_documents(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Semantic vector search across all uploaded documents."""
    if not q or len(q.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Query must be at least 3 characters"
        )

    results = await VectorService.search_similar(db, q, limit=5)

    return {
        "query"  : q,
        "total"  : len(results),
        "results": results
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Get details of a specific document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    result = await db.execute(
        select(Document).where(
            Document.id == doc_uuid,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id"            : str(document.id),
        "filename"      : document.original_name,
        "file_type"     : document.file_type.value,
        "file_size_kb"  : round(document.file_size / 1024, 2),
        "status"        : document.status.value,
        "summary"       : document.summary,
        "extracted_text": document.extracted_text[:500] if document.extracted_text else None,
        "duration"      : document.duration,
        "created_at"    : document.created_at.isoformat() if document.created_at else None
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Delete a document and its file from disk."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    result = await db.execute(
        select(Document).where(
            Document.id == doc_uuid,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    if document.transcript_path and os.path.exists(document.transcript_path):
        os.remove(document.transcript_path)

    await db.delete(document)
    return {"message": f"Document '{document.original_name}' deleted successfully"}


@router.get("/documents/{document_id}/file")
async def serve_file(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  # pragma: no cover
    """Serve the original uploaded file for a document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    result = await db.execute(
        select(Document).where(
            Document.id == doc_uuid,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = document.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        if document.file_type == FileType.VIDEO:
            mime_type = "video/mp4"
        elif document.file_type == FileType.AUDIO:
            mime_type = "audio/mpeg"
        elif document.file_type == FileType.PDF:
            mime_type = "application/pdf"
        else:
            mime_type = "application/octet-stream"

    return FileResponse(
        path       = file_path,
        media_type = mime_type,
        filename   = document.original_name
    )