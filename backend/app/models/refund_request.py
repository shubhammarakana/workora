from sqlalchemy import Column, Integer, BigInteger, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    refund_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=False, index=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=False)
    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="Pending Approval", index=True)
    approved_by = Column(String(150), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="refund_requests")
    shipment = relationship("Shipment", back_populates="refund_requests")
    invoice = relationship("Invoice", back_populates="refund_requests")

    def __repr__(self):
        return f"<RefundRequest {self.refund_id} - Amount: {self.amount} ({self.status})>"
