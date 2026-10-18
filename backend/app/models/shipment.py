from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, Numeric, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import relationship
from ..database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=False, index=True)
    tracking_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    current_location = Column(String(255), nullable=True)
    origin = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)
    expected_delivery = Column(Date, nullable=True)
    actual_delivery = Column(Date, nullable=True)
    package_type = Column(String(100), nullable=True)
    weight_kg = Column(Numeric(10, 2), nullable=True)
    shipping_charge = Column(Numeric(10, 2), nullable=True)
    carrier = Column(String(100), nullable=True, default="LogiFlow Express")
    last_update = Column(String(255), nullable=True)
    delay_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="shipments")
    delivery_events = relationship("DeliveryEvent", back_populates="shipment", cascade="all, delete-orphan")
    delivery_assignments = relationship("DeliveryAssignment", back_populates="shipment", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="shipment", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="shipment", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="shipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shipment {self.shipment_id} - {self.status}>"
