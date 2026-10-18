from pydantic import BaseModel
from typing import Optional
import datetime

class InvoiceOut(BaseModel):
    id: int
    invoice_id: str
    customer_id: int
    shipment_id: int | str
    amount: Optional[float] = None
    tax_amount: Optional[float] = 0.0
    total_amount: Optional[float] = None
    payment_status: str
    invoice_date: datetime.date | str
    due_date: Optional[datetime.date | str] = None

    class Config:
        from_attributes = True
