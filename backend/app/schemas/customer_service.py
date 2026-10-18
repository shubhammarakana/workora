from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class CustomerServiceChatRequest(BaseModel):
    message: str
    shipment_id: Optional[str] = None

class HumanSupportCreate(BaseModel):
    shipment_id: Optional[str] = None
    notes: Optional[str] = None

class HumanSupportOut(BaseModel):
    id: int
    request_id: str
    customer_id: Optional[int] = None
    shipment_id: Optional[int | str] = None
    status: str
    priority: str
    notes: Optional[str] = None
    created_at: Optional[Any] = None

    class Config:
        from_attributes = True

class CustomerServiceChatResponse(BaseModel):
    message: str
    intent: str
    employee_used: str = "Customer Service Employee"
    shipment_id: Optional[str] = None
    ticket_id: Optional[str] = None
    support_request_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    context_panel: Optional[Dict[str, Any]] = None
