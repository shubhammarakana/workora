from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.invoice import Invoice
from ..models.customer import Customer
from ..schemas.invoice import InvoiceOut
from ..auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

@router.get("", response_model=List[InvoiceOut], summary="List invoices")
def list_invoices(
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    if current_user:
        return db.query(Invoice).filter(Invoice.customer_id == current_user.id).all()
    return db.query(Invoice).all()

@router.get("/{invoice_id}", response_model=InvoiceOut, summary="Get invoice by ID")
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id.upper()).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Invoice not found", "code": "INVOICE_NOT_FOUND"}
        )
    if current_user and invoice.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied to requested invoice", "code": "FORBIDDEN"}
        )
    return invoice
