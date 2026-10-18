from pydantic import BaseModel
from typing import Optional
import datetime

class ShipmentBase(BaseModel):
    shipment_id: str
    status: str
    current_location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    expected_delivery: Optional[datetime.date | str] = None
    actual_delivery: Optional[datetime.date | str] = None
    tracking_number: Optional[str] = None
    package_type: Optional[str] = None
    weight_kg: Optional[float] = None
    shipping_charge: Optional[float] = None
    carrier: Optional[str] = "LogiFlow Express"
    last_update: Optional[str] = None
    delay_reason: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    customer_id: int

class ShipmentOut(ShipmentBase):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    timeline: Optional[list] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
