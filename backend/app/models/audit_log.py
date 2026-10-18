from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=True, index=True)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(100), nullable=True)
    result = Column(String(50), nullable=True)
    details = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())

    # Relationship
    customer = relationship("Customer", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} - {self.result}>"
