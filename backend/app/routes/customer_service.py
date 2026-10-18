from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..models.customer import Customer
from ..models.ticket import Ticket
from ..models.human_support import HumanSupportRequest
from ..schemas.customer_service import (
    CustomerServiceChatRequest,
    CustomerServiceChatResponse,
    HumanSupportCreate,
    HumanSupportOut
)
from ..schemas.ticket import TicketCreate, TicketOut
from ..services.customer_service_service import CustomerServiceService
from ..auth import get_optional_current_user

router = APIRouter(prefix="/api", tags=["Customer Service"])

@router.post("/customer-service/chat", response_model=CustomerServiceChatResponse, summary="Process chat message via Customer Service Employee")
def customer_service_chat(
    req: CustomerServiceChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Central Customer Service AI Employee endpoint.
    Performs intent classification, entity extraction, service routing, context panel payload generation, and audit logging.
    """
    return CustomerServiceService.process_customer_service_message(
        message=req.message,
        db=db,
        current_user=current_user,
        provided_shipment_id=req.shipment_id
    )

@router.post("/human-support", response_model=HumanSupportOut, summary="Create human support escalation request")
def create_human_support(
    req: HumanSupportCreate,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Create a new human support request (e.g. SUP-10025).
    """
    import random
    sup_id = f"SUP-{random.randint(20000, 99999)}"
    cust_id = current_user.id if current_user else 1

    sup_req = HumanSupportRequest(
        request_id=sup_id,
        customer_id=cust_id,
        status="Waiting for Agent",
        priority="Normal",
        notes=req.notes or "Escalation requested via Web Chat"
    )
    try:
        db.add(sup_req)
        db.commit()
        db.refresh(sup_req)
    except Exception:
        db.rollback()
        sup_req = db.query(HumanSupportRequest).filter(HumanSupportRequest.customer_id == cust_id).first()
    return sup_req
