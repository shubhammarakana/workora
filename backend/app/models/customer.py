from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), default="customer", nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationships
    shipments = relationship("Shipment", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.customer_id} - {self.name}>"
