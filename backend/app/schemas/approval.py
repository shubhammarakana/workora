from pydantic import BaseModel, Field
from typing import List, Optional, Union
import datetime

class ApprovalCreate(BaseModel):
    request_type: str = Field(..., example="refund") # refund, address_change, cancellation, billing_change
    employee: str = Field(..., example="Billing Employee")
    customer_id: Optional[Union[int, str]] = None
    shipment_id: Optional[str] = None
    invoice_id: Optional[str] = None
    amount: Optional[float] = Field(None, example=2000.0)
    reason: Optional[str] = Field(None, example="Damaged shipment")
    requested_action: Optional[str] = Field(None, example="Refund ₹2,000")
    priority: Optional[str] = Field("Medium", example="Medium")

class ApprovalOut(BaseModel):
    approval_id: str = Field(..., example="APR-10024")
    request_type: str = Field(..., example="refund")
    employee: str = Field(..., example="Billing Employee")
    customer_id: Optional[Union[int, str]] = None
    customer_name: Optional[str] = Field("Demo Customer", example="Rahul Patel")
    shipment_id: Optional[str] = Field(None, example="SL1004")
    invoice_id: Optional[str] = Field(None, example="INV-2045")
    amount: Optional[float] = Field(None, example=2000.0)
    reason: Optional[str] = Field(None, example="Damaged shipment")
    requested_action: Optional[str] = Field(None, example="Refund ₹2,000")
    status: str = Field("Pending Approval", example="Pending Approval")
    priority: str = Field("Medium", example="Medium")
    created_at: Optional[Union[datetime.datetime, str]] = None
    updated_at: Optional[Union[datetime.datetime, str]] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[Union[datetime.datetime, str]] = None
    review_comment: Optional[str] = None
    ai_recommendation: Optional[str] = "Approve"
    risk_level: Optional[str] = "Medium"

    class Config:
        from_attributes = True

class ApprovalDecision(BaseModel):
    reason: Optional[str] = None
    review_comment: Optional[str] = None

class ApprovalStats(BaseModel):
    pending_approvals: int = 12
    approved_today: int = 18
    rejected_today: int = 3
    avg_approval_time_min: float = 8.0
    label: str = "Demo Data"
