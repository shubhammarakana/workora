from sqlalchemy import Column, Integer, BigInteger, String, Text, Date, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..database import Base

class DeliveryRecord(Base):
    __tablename__ = "delivery_records"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    delivery_id = Column(String(50), unique=True, nullable=False, index=True)
    shipment_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.id"), nullable=True, index=True)
    
    delivery_status = Column(String(50), nullable=False, default="In Transit", index=True)
    expected_date = Column(Date, nullable=True)
    delivery_window = Column(String(100), nullable=True)
    delivery_address = Column(String(255), nullable=True)
    
    driver_id = Column(String(50), nullable=True)
    driver_name = Column(String(150), nullable=True)
    
    attempt_count = Column(Integer, default=0)
    last_attempt = Column(String(100), nullable=True)
    
    exception_type = Column(String(100), nullable=True)
    exception_reason = Column(String(255), nullable=True)
    
    available_slots = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    reschedule_allowed = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now(), default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=func.now(), onupdate=func.now())

    # Relationship
    customer = relationship("Customer")

    def __repr__(self):
        return f"<DeliveryRecord {self.delivery_id} for {self.shipment_id} - {self.delivery_status}>"
