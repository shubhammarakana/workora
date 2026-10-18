from pydantic import BaseModel
from typing import Optional
import datetime

class TicketCreate(BaseModel):
    shipment_id: Optional[str] = None
    issue_type: Optional[str] = "Damaged Package"
    category: Optional[str] = "Complaint"
    issue: str
    priority: Optional[str] = "Normal"

class TicketOut(BaseModel):
    id: int
    ticket_id: str
    customer_id: int
    shipment_id: Optional[int | str] = None
    shipment_code: Optional[str] = None
    issue_type: Optional[str] = "Damaged Package"
    category: Optional[str] = "Complaint"
    issue: str
    priority: Optional[str] = "Normal"
    status: str
    assigned_to: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
