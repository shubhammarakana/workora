from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    active_employee: Optional[str] = None
    customer_id: Optional[str] = None
    session_id: Optional[str] = "demo-session-001"

class ChatResponse(BaseModel):
    message: str
    intent: str
    shipment_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
