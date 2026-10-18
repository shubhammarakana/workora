from sqlalchemy import Column, Integer, BigInteger, String, Date, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=False, index=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=False, index=True)
    
    shipping_charge = Column(Numeric(12, 2), nullable=False)
    tax = Column(Numeric(12, 2), default=0.0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    payment_status = Column(String(50), default="Pending", index=True)
    payment_date = Column(Date, nullable=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    currency = Column(String(10), default="INR")
    
    refund_status = Column(String(50), nullable=True)
    refund_amount = Column(Numeric(12, 2), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    shipment = relationship("Shipment", back_populates="invoices")
    refund_requests = relationship("RefundRequest", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice {self.invoice_id} - Total: {self.total_amount} ({self.payment_status})>"
