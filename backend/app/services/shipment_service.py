from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.shipment import Shipment
from ..models.customer import Customer

class ShipmentService:
    @staticmethod
    def get_shipment_by_id(db: Session, shipment_id: str) -> Optional[Shipment]:
        return db.query(Shipment).filter(Shipment.shipment_id == shipment_id.upper()).first()

    @staticmethod
    def get_customer_shipments(db: Session, customer_id: int) -> List[Shipment]:
        return db.query(Shipment).filter(Shipment.customer_id == customer_id).all()

    @staticmethod
    def verify_ownership(shipment: Shipment, customer: Customer) -> bool:
        return shipment.customer_id == customer.id
