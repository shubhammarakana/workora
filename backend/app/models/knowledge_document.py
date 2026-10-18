from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, func
from ..database import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    document_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeDocument {self.document_id} - {self.title}>"
