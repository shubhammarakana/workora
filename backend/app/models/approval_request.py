from sqlalchemy import Column, Integer, BigInteger, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    approval_id = Column(String(50), unique=True, nullable=False, index=True)
    request_type = Column(String(50), nullable=False, index=True) # refund, address_change, cancellation, billing_change
    employee = Column(String(100), nullable=False) # Billing Employee, Delivery Employee, etc.
    
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=True, index=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=True)
    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.id"), nullable=True)
    
    amount = Column(Numeric(12, 2), nullable=True)
    reason = Column(Text, nullable=True)
    requested_action = Column(String(255), nullable=True)
    
    status = Column(String(50), default="Pending Approval", index=True) # Pending Approval, Approved, Rejected, Processing, Completed, Cancelled
    priority = Column(String(20), default="Medium", index=True) # Low, Medium, High, Critical
    
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), default=func.now())
    
    reviewed_by = Column(String(150), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    # Relationships
    customer = relationship("Customer")
    shipment = relationship("Shipment")
    invoice = relationship("Invoice")

    def __repr__(self):
        return f"<ApprovalRequest {self.approval_id} - {self.request_type} ({self.status})>"
