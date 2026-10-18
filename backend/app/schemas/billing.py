from pydantic import BaseModel, Field
from typing import List, Optional, Union
import datetime

class InvoiceOut(BaseModel):
    invoice_id: str = Field(..., example="INV-2045")
    customer_id: Optional[int] = None
    shipment_id: Optional[Union[int, str]] = None
    shipment_code: Optional[str] = Field(None, example="SL1004")
    customer_name: Optional[str] = Field(None, example="Demo Customer")
    shipping_charge: float = Field(..., example=1050.0)
    tax: float = Field(..., example=200.0)
    total_amount: float = Field(..., example=1250.0)
    payment_status: str = Field(..., example="Paid")
    payment_date: Optional[Union[datetime.date, str]] = None
    invoice_date: Optional[Union[datetime.date, str]] = None
    due_date: Optional[Union[datetime.date, str]] = None
    currency: str = Field("INR", example="INR")
    refund_status: Optional[str] = None
    refund_amount: Optional[float] = None

    class Config:
        from_attributes = True

class BillingHistoryOut(BaseModel):
    customer_id: Union[int, str]
    invoices: List[InvoiceOut]

class PaymentReminderRequest(BaseModel):
    invoice_id: Optional[str] = None
    shipment_id: Optional[str] = None

class PaymentReminderResponse(BaseModel):
    reminder_id: str = Field(..., example="REM-90412")
    invoice_id: str = Field(..., example="INV-2045")
    amount: float = Field(..., example=1250.0)
    due_date: Optional[str] = None
    status: str = Field("Created", example="Created")
    message: str

class RefundRequestCreate(BaseModel):
    invoice_id: Optional[str] = None
    shipment_id: Optional[str] = None
    amount: Optional[float] = None
    requested_amount: Optional[float] = None
    reason: str = Field(..., example="Damaged package during transit")

    @property
    def get_amount(self) -> float:
        return self.amount if self.amount is not None else (self.requested_amount or 0.0)

class RefundRequestOut(BaseModel):
    request_id: str = Field(..., example="REF-10024")
    invoice_id: str = Field(..., example="INV-2045")
    shipment_id: str = Field(..., example="SL1004")
    requested_amount: float = Field(..., example=1250.0)
    reason: str = Field(..., example="Damaged package during transit")
    status: str = Field("Pending Review", example="Pending Review")
    requires_human_approval: bool = True
    message: str

class BillingSupportRequest(BaseModel):
    invoice_id: Optional[str] = None
    shipment_id: Optional[str] = None
    issue_type: Optional[str] = Field("Billing Complaint", example="Billing Complaint")
    message: Optional[str] = None
    issue_description: Optional[str] = None

class BillingSupportResponse(BaseModel):
    request_id: str = Field(..., example="LGT-9012")
    invoice_id: Optional[str] = None
    status: str = Field("Created", example="Created")
    message: str
