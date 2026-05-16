# backend/app/models/chat.py

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class MessageRole(str, enum.Enum):
    USER      = "user"
    ASSISTANT = "assistant"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # nullable for backward compat
    title       = Column(String(255), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
    messages    = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession {self.id}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id         = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role               = Column(Enum(MessageRole), nullable=False)
    content            = Column(Text, nullable=False)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    confidence_score   = Column(Float, nullable=True)
    timestamps         = Column(JSON, nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    session            = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}>"