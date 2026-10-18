from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    conversation_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    channel = Column(String(50), default="web")
    status = Column(String(50), default="Active")
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation {self.conversation_id} - Channel: {self.channel}>"
