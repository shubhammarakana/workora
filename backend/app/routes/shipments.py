from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.shipment import Shipment
from ..models.customer import Customer
from ..schemas.shipment import ShipmentOut
from ..auth import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/shipments", tags=["Shipments"])

def _format_shipment(s: Shipment) -> dict:
    cust_name = s.customer.name if s.customer else "Demo Customer"
    timeline_events = []
    if s.delivery_events:
        for ev in sorted(s.delivery_events, key=lambda x: x.event_time or x.id):
            timeline_events.append({
                "title": ev.status,
                "time": ev.event_time.strftime("%d %b %Y, %I:%M %p") if ev.event_time else "Recently",
                "location": ev.location or "",
                "description": ev.description or ""
            })
    
    return {
        "id": s.id,
        "shipment_id": s.shipment_id,
        "customer_id": s.customer_id,
        "customer_name": cust_name,
        "status": s.status,
        "current_location": s.current_location,
        "origin": s.origin,
        "destination": s.destination,
        "expected_delivery": str(s.expected_delivery) if s.expected_delivery else None,
        "actual_delivery": str(s.actual_delivery) if s.actual_delivery else None,
        "tracking_number": s.tracking_number,
        "package_type": s.package_type,
        "weight_kg": float(s.weight_kg) if s.weight_kg is not None else None,
        "shipping_charge": float(s.shipping_charge) if s.shipping_charge is not None else None,
        "carrier": s.carrier or "LogiFlow Express",
        "last_update": s.last_update or (s.current_location if s.current_location else "Updated recently"),
        "delay_reason": s.delay_reason,
        "timeline": timeline_events,
        "created_at": s.created_at,
        "updated_at": s.updated_at
    }

@router.get("", response_model=List[ShipmentOut], summary="List shipments")
def list_shipments(
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve all shipments for the currently authenticated customer,
    or all demo shipments if unauthenticated in prototype mode.
    """
    if current_user:
        shipments = db.query(Shipment).filter(Shipment.customer_id == current_user.id).all()
    else:
        shipments = db.query(Shipment).all()
    return [_format_shipment(s) for s in shipments]

@router.get("/{shipment_id}", response_model=ShipmentOut, summary="Get shipment by ID")
def get_shipment(
    shipment_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Retrieve tracking details for a specific shipment ID (e.g. SL1004).
    Enforces authorization check if authenticated.
    """
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id.upper()).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"I couldn't find shipment {shipment_id.upper()}. Please check the shipment ID and try again.", "code": "SHIPMENT_NOT_FOUND"}
        )
    
    # Ownership authorization check
    if current_user and shipment.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied to requested shipment", "code": "FORBIDDEN"}
        )
        
    return _format_shipment(shipment)
