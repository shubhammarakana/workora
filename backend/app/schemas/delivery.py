from pydantic import BaseModel, Field
from typing import List, Optional, Union
import datetime

class DeliveryRescheduleRequest(BaseModel):
    date: str = Field(..., example="2026-10-09")
    time_slot: str = Field(..., example="14:00-17:00")

class DeliveryRescheduleResponse(BaseModel):
    request_id: str = Field(..., example="DLV-10024")
    shipment_id: str = Field(..., example="SL1004")
    status: str = Field(..., example="confirmed")
    new_delivery_date: Optional[str] = None
    time_slot: Optional[str] = None

class DeliveryAttemptRequest(BaseModel):
    notes: Optional[str] = None

class DeliveryAttemptResponse(BaseModel):
    request_id: str = Field(..., example="DLV-10025")
    shipment_id: str = Field(..., example="SL1003")
    status: str = Field(..., example="scheduled")
    message: str

class AddressChangeRequest(BaseModel):
    new_address: str = Field(..., example="B-402, Riverfront Heights, Ashram Road, Ahmedabad, GJ")
    reason: Optional[str] = None

class AddressChangeResponse(BaseModel):
    request_id: str = Field(..., example="DLV-10026")
    shipment_id: str = Field(..., example="SL1004")
    status: str = Field(..., example="waiting_for_approval")
    requires_human_approval: bool = True
    message: str

class DeliverySupportRequest(BaseModel):
    shipment_id: str = Field(..., example="SL1004")
    issue_type: str = Field(..., example="Driver Coordination")
    message: str = Field(..., example="Request to contact driver regarding delivery instructions.")

class DeliverySupportResponse(BaseModel):
    request_id: str = Field(..., example="DLV-10027")
    shipment_id: str = Field(..., example="SL1004")
    status: str = Field(..., example="created")
    message: str

class DeliverySlotsOut(BaseModel):
    shipment_id: str
    reschedule_allowed: bool
    available_slots: List[str]

class DeliveryOut(BaseModel):
    delivery_id: str
    shipment_id: str
    customer_id: Optional[int] = None
    delivery_status: str
    expected_date: Optional[Union[datetime.date, str]] = None
    delivery_window: Optional[str] = None
    delivery_address: Optional[str] = None
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    attempt_count: int = 0
    last_attempt: Optional[str] = None
    exception_type: Optional[str] = None
    exception_reason: Optional[str] = None
    available_slots: Optional[List[str]] = []
    reschedule_allowed: bool = True
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
