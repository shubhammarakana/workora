from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("conversations.id"), nullable=False, index=True)
    sender_type = Column(String(30), nullable=False)  # customer, ai, human
    message = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage [{self.sender_type}] {self.intent}: {self.message[:30]}...>"
