from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class HumanSupportRequest(Base):
    __tablename__ = "human_support_requests"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    request_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=True, index=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=True, index=True)
    status = Column(String(50), default="Waiting for Agent", index=True)
    priority = Column(String(30), default="Normal")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    shipment = relationship("Shipment")

    def __repr__(self):
        return f"<HumanSupportRequest {self.request_id} - {self.status}>"
