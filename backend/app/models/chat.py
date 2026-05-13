# backend/app/models/chat.py

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base
from app.services.vector_service import VectorService

class MessageRole(str, enum.Enum):
    USER      = "user"
    ASSISTANT = "assistant"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title       = Column(String(255), nullable=True)           # auto-generated from first message
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    messages    = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession {self.id}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id   = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role         = Column(Enum(MessageRole), nullable=False)
    content      = Column(Text, nullable=False)

    # For assistant messages — source info
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    confidence_score   = Column(Float, nullable=True)

    # Timestamp info (for audio/video answers)
    # e.g. [{"start": 12.5, "end": 24.0, "text": "..."}]
    timestamps   = Column(JSON, nullable=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session      = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}>"