from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class DeliveryEvent(Base):
    __tablename__ = "delivery_events"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    shipment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("shipments.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    event_time = Column(DateTime, server_default=func.now(), default=func.now())

    # Relationship
    shipment = relationship("Shipment", back_populates="delivery_events")

    def __repr__(self):
        return f"<DeliveryEvent {self.shipment_id} - {self.status} at {self.location}>"
