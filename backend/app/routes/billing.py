from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.customer import Customer
from ..auth import get_optional_current_user
from ..schemas.billing import (
    InvoiceOut,
    BillingHistoryOut,
    PaymentReminderRequest,
    PaymentReminderResponse,
    RefundRequestCreate,
    RefundRequestOut,
    BillingSupportRequest,
    BillingSupportResponse
)
from ..services.billing_service import BillingService

router = APIRouter(prefix="/api/billing", tags=["Billing Employee"])

@router.get("/invoice/{invoice_id}", response_model=InvoiceOut, summary="Get invoice by Invoice ID")
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve invoice details for a specific invoice ID (e.g. INV-2045).
    Returns 404 if not found, 403 if unauthorized for requested invoice.
    """
    return BillingService.get_invoice(invoice_id, db, current_user)

@router.get("/shipment/{shipment_id}", response_model=InvoiceOut, summary="Get invoice by Shipment ID")
def get_invoice_by_shipment(
    shipment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve invoice associated with a specific shipment ID (e.g. SL1004).
    """
    return BillingService.get_invoice_by_shipment(shipment_id, db, current_user)

@router.get("/history/{customer_id}", response_model=BillingHistoryOut, summary="Get customer billing history")
def get_billing_history(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve authorized customer billing history.
    """
    return BillingService.get_billing_history(customer_id, db, current_user)

@router.post("/reminder", response_model=PaymentReminderResponse, summary="Create payment reminder")
def create_payment_reminder(
    req: PaymentReminderRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Create a payment reminder for a pending invoice.
    """
    return BillingService.create_payment_reminder(req, db, current_user)

@router.post("/refund-request", response_model=RefundRequestOut, summary="Submit refund request")
def submit_refund_request(
    req: RefundRequestCreate,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Submit a refund request. Requires Human Approval.
    Validates amount does not exceed invoice total.
    """
    return BillingService.request_refund(req, db, current_user)

@router.get("/refund/{request_id}", response_model=RefundRequestOut, summary="Get refund request status")
def get_refund_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve status of a refund request by ID (e.g. REF-10024).
    """
    return BillingService.get_refund_request(request_id, db)

@router.post("/support", response_model=BillingSupportResponse, summary="Create billing support request")
def create_billing_support(
    req: BillingSupportRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Create a billing support ticket for billing complaints or questions.
    """
    return BillingService.create_support_request(req, db, current_user)
