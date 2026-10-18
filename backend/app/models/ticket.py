from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=False, index=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=True, index=True)
    issue_type = Column(String(100), nullable=False, default="General Inquiry")
    category = Column(String(100), nullable=False, default="Complaint")
    issue = Column(Text, nullable=False)
    priority = Column(String(30), default="Normal")
    status = Column(String(50), default="Pending Review", index=True)
    assigned_to = Column(String(150), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    shipment = relationship("Shipment", back_populates="tickets")

    def __repr__(self):
        return f"<Ticket {self.ticket_id} - {self.issue_type} ({self.status})>"
