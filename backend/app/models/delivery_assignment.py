from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=False, index=True)
    driver_name = Column(String(150), nullable=True)
    driver_phone = Column(String(20), nullable=True)
    vehicle_number = Column(String(50), nullable=True)
    vehicle_type = Column(String(100), nullable=True)
    assignment_status = Column(String(50), default="Assigned")
    scheduled_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), default=func.now())

    # Relationship
    shipment = relationship("Shipment", back_populates="delivery_assignments")

    def __repr__(self):
        return f"<DeliveryAssignment {self.shipment_id} - Driver: {self.driver_name}>"
