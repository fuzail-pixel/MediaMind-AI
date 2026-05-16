# backend/app/models/document.py

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
import enum
from app.core.database import Base


class FileType(str, enum.Enum):
    PDF   = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


class ProcessingStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


class Document(Base):
    __tablename__ = "documents"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # nullable for backward compat
    filename        = Column(String(255), nullable=False)
    original_name   = Column(String(255), nullable=False)
    file_type       = Column(Enum(FileType), nullable=False)
    file_size       = Column(Integer, nullable=False)
    file_path       = Column(String(500), nullable=False)
    extracted_text  = Column(Text, nullable=True)
    summary         = Column(Text, nullable=True)
    duration        = Column(Float, nullable=True)
    transcript_path = Column(String(500), nullable=True)
    embedding       = Column(Vector(1536), nullable=True)
    status          = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    error_message   = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Document {self.original_name} ({self.file_type})>"