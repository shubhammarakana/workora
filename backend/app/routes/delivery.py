from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.customer import Customer
from ..auth import get_optional_current_user
from ..schemas.delivery import (
    DeliveryOut,
    DeliverySlotsOut,
    DeliveryRescheduleRequest,
    DeliveryRescheduleResponse,
    DeliveryAttemptRequest,
    DeliveryAttemptResponse,
    AddressChangeRequest,
    AddressChangeResponse,
    DeliverySupportRequest,
    DeliverySupportResponse
)
from ..services.delivery_service import DeliveryService

router = APIRouter(prefix="/api/delivery", tags=["Delivery Operations Employee"])

@router.get("/{shipment_id}", response_model=DeliveryOut, summary="Get delivery record by Shipment ID")
def get_delivery_status(
    shipment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve delivery information for a specific shipment ID (e.g. SL1004).
    Returns 404 if shipment is not found, 403 if unauthorized.
    """
    return DeliveryService.get_delivery_record(shipment_id, db, current_user)

@router.get("/{shipment_id}/slots", response_model=DeliverySlotsOut, summary="Get available delivery slots")
def get_delivery_slots(
    shipment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Query available delivery slots for a shipment.
    """
    return DeliveryService.get_slots(shipment_id, db, current_user)

@router.post("/{shipment_id}/reschedule", response_model=DeliveryRescheduleResponse, summary="Reschedule delivery slot")
def reschedule_delivery(
    shipment_id: str,
    req: DeliveryRescheduleRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Reschedule a delivery slot. Returns confirmation with request ID.
    Only returns confirmed status when backend actually updates delivery record.
    """
    cust_id = current_user.id if current_user else None
    return DeliveryService.reschedule_delivery(shipment_id, req, db, cust_id)

@router.post("/{shipment_id}/attempt", response_model=DeliveryAttemptResponse, summary="Request new delivery attempt")
def request_delivery_attempt(
    shipment_id: str,
    req: DeliveryAttemptRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Request another delivery attempt for failed/unsuccessful deliveries (e.g. SL1003).
    """
    cust_id = current_user.id if current_user else None
    return DeliveryService.request_new_attempt(shipment_id, req, db, cust_id)

@router.post("/{shipment_id}/address-change", response_model=AddressChangeResponse, summary="Request delivery address change")
def request_address_change(
    shipment_id: str,
    req: AddressChangeRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Submit a delivery address change request. Requires Human Approval.
    """
    cust_id = current_user.id if current_user else None
    return DeliveryService.request_address_change(shipment_id, req, db, cust_id)

@router.post("/support", response_model=DeliverySupportResponse, summary="Create delivery support request")
def create_delivery_support(
    req: DeliverySupportRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Create a delivery support ticket (e.g. driver coordination, delivery inquiry).
    Does NOT expose private driver contact information.
    """
    cust_id = current_user.id if current_user else None
    return DeliveryService.create_support_request(req, db, cust_id)
