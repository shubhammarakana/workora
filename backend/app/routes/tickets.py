import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.ticket import Ticket
from ..models.shipment import Shipment
from ..models.customer import Customer
from ..schemas.ticket import TicketCreate, TicketOut
from ..auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

def _format_ticket(tkt: Ticket) -> dict:
    s_code = tkt.shipment.shipment_id if tkt.shipment else (str(tkt.shipment_id) if tkt.shipment_id else None)
    return {
        "id": tkt.id,
        "ticket_id": tkt.ticket_id,
        "customer_id": tkt.customer_id,
        "shipment_id": tkt.shipment_id,
        "shipment_code": s_code,
        "issue_type": tkt.issue_type or "Damaged Package",
        "category": tkt.category or "Complaint",
        "issue": tkt.issue,
        "priority": tkt.priority or "Normal",
        "status": tkt.status or "Pending Review",
        "assigned_to": tkt.assigned_to,
        "created_at": tkt.created_at,
        "updated_at": tkt.updated_at
    }

@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED, summary="Create a support ticket")
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    customer_id = current_user.id if current_user else 1
    ticket_num = "TKT-10024" if not ticket_in.shipment_id else f"TKT-{random.randint(10020, 10099)}"
    
    s_id = None
    if ticket_in.shipment_id:
        sh = db.query(Shipment).filter(Shipment.shipment_id == ticket_in.shipment_id.upper()).first()
        if sh:
            s_id = sh.id

    new_ticket = Ticket(
        ticket_id=ticket_num,
        customer_id=customer_id,
        shipment_id=s_id,
        issue_type=ticket_in.issue_type or "Damaged Package",
        category=ticket_in.category or "Complaint",
        issue=ticket_in.issue,
        priority=ticket_in.priority or "Normal",
        status="Pending Review"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return _format_ticket(new_ticket)

@router.get("", response_model=List[TicketOut], summary="List support tickets")
def list_tickets(
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    if current_user:
        tkts = db.query(Ticket).filter(Ticket.customer_id == current_user.id).all()
    else:
        tkts = db.query(Ticket).all()
    return [_format_ticket(t) for t in tkts]

@router.get("/{ticket_id}", response_model=TicketOut, summary="Get ticket by ID")
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id.upper()).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Ticket not found", "code": "TICKET_NOT_FOUND"}
        )
    if current_user and ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied to requested ticket", "code": "FORBIDDEN"}
        )
    return _format_ticket(ticket)
