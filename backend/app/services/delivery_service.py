import random
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.delivery_record import DeliveryRecord
from ..models.shipment import Shipment
from ..models.audit_log import AuditLog
from ..models.customer import Customer
from ..schemas.delivery import (
    DeliveryRescheduleRequest,
    DeliveryRescheduleResponse,
    DeliveryAttemptRequest,
    DeliveryAttemptResponse,
    AddressChangeRequest,
    AddressChangeResponse,
    DeliverySupportRequest,
    DeliverySupportResponse,
    DeliverySlotsOut,
    DeliveryOut
)

class DeliveryService:
    @staticmethod
    def _generate_req_id() -> str:
        return f"DLV-{random.randint(10000, 99999)}"

    @classmethod
    def get_delivery_record(cls, shipment_id: str, db: Session, current_user: Optional[Customer] = None) -> DeliveryRecord:
        shipment_id_clean = shipment_id.strip().upper()
        record = db.query(DeliveryRecord).filter(DeliveryRecord.shipment_id == shipment_id_clean).first()
        if not record:
            # Check if valid shipment exists in Shipment table
            shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id_clean).first()
            if not shipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": f"I couldn't find shipment {shipment_id_clean}. Please check the shipment ID and try again.", "code": "SHIPMENT_NOT_FOUND"}
                )
            # Auto-create delivery record dynamically for existing shipment
            record = DeliveryRecord(
                delivery_id=f"DLV-{random.randint(1000, 9999)}",
                shipment_id=shipment.shipment_id,
                customer_id=shipment.customer_id,
                delivery_status=shipment.status,
                expected_date=shipment.expected_delivery,
                delivery_window="2:00 PM – 5:00 PM",
                delivery_address=shipment.destination,
                driver_id="DRV-804",
                driver_name="Ramesh Solanki",
                attempt_count=0,
                available_slots=["9 October — 10 AM–1 PM", "9 October — 2 PM–5 PM", "10 October — 10 AM–1 PM"],
                reschedule_allowed=(shipment.status.lower() not in ["delivered", "out for delivery"])
            )
            db.add(record)
            db.commit()
            db.refresh(record)

        if current_user and getattr(current_user, "role", "customer").lower() != "admin":
            if record.customer_id and record.customer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "Access denied to requested delivery record", "code": "FORBIDDEN"}
                )

        return record

    @classmethod
    def get_slots(cls, shipment_id: str, db: Session, current_user: Optional[Customer] = None) -> DeliverySlotsOut:
        record = cls.get_delivery_record(shipment_id, db, current_user)
        slots = record.available_slots if record.available_slots else [
            "9 October — 10 AM–1 PM",
            "9 October — 2 PM–5 PM",
            "10 October — 10 AM–1 PM"
        ]
        return DeliverySlotsOut(
            shipment_id=record.shipment_id,
            reschedule_allowed=record.reschedule_allowed,
            available_slots=slots if record.reschedule_allowed else []
        )

    @classmethod
    def reschedule_delivery(
        cls,
        shipment_id: str,
        req: DeliveryRescheduleRequest,
        db: Session,
        customer_id: Optional[int] = None
    ) -> DeliveryRescheduleResponse:
        record = cls.get_delivery_record(shipment_id, db)

        if not record.reschedule_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Rescheduling is not allowed for shipment {record.shipment_id} in state '{record.delivery_status}'.", "code": "RESCHEDULE_NOT_ALLOWED"}
            )

        req_id = cls._generate_req_id()
        
        # Parse date if possible
        try:
            new_date = datetime.datetime.strptime(req.date, "%Y-%m-%d").date()
            record.expected_date = new_date
        except Exception:
            pass

        record.delivery_window = req.time_slot
        record.delivery_status = "In Transit"
        record.exception_type = None
        record.exception_reason = None
        
        # Also update Shipment table
        shipment = db.query(Shipment).filter(Shipment.shipment_id == record.shipment_id).first()
        if shipment:
            shipment.expected_delivery = record.expected_date
            shipment.last_update = f"Delivery rescheduled to {req.date} ({req.time_slot})"

        # Write Audit Log
        audit = AuditLog(
            customer_id=customer_id or record.customer_id,
            action="Reschedule Delivery",
            entity_type="Shipment",
            entity_id=record.shipment_id,
            result="Confirmed",
            details={
                "delivery_employee": "🚚 Delivery Employee",
                "request_id": req_id,
                "slot_selected": f"{req.date} · {req.time_slot}",
                "new_date": str(record.expected_date),
                "time_slot": req.time_slot
            }
        )
        db.add(audit)
        db.commit()

        return DeliveryRescheduleResponse(
            request_id=req_id,
            shipment_id=record.shipment_id,
            status="confirmed",
            new_delivery_date=str(record.expected_date),
            time_slot=req.time_slot
        )

    @classmethod
    def request_new_attempt(
        cls,
        shipment_id: str,
        req: DeliveryAttemptRequest,
        db: Session,
        customer_id: Optional[int] = None
    ) -> DeliveryAttemptResponse:
        record = cls.get_delivery_record(shipment_id, db)
        req_id = cls._generate_req_id()

        record.delivery_status = "Out for Delivery"
        record.attempt_count += 1
        record.exception_type = None
        record.exception_reason = None

        # Update Shipment
        shipment = db.query(Shipment).filter(Shipment.shipment_id == record.shipment_id).first()
        if shipment:
            shipment.status = "Out for Delivery"
            shipment.last_update = "New delivery attempt requested by customer"

        audit = AuditLog(
            customer_id=customer_id or record.customer_id,
            action="Request New Delivery Attempt",
            entity_type="Shipment",
            entity_id=record.shipment_id,
            result="Scheduled",
            details={
                "delivery_employee": "🚚 Delivery Employee",
                "request_id": req_id,
                "attempt_number": record.attempt_count,
                "notes": req.notes
            }
        )
        db.add(audit)
        db.commit()

        return DeliveryAttemptResponse(
            request_id=req_id,
            shipment_id=record.shipment_id,
            status="scheduled",
            message=f"New delivery attempt scheduled for shipment {record.shipment_id}."
        )

    @classmethod
    def request_address_change(
        cls,
        shipment_id: str,
        req: AddressChangeRequest,
        db: Session,
        customer_id: Optional[int] = None
    ) -> AddressChangeResponse:
        record = cls.get_delivery_record(shipment_id, db)
        req_id = cls._generate_req_id()

        # Create corresponding ApprovalRequest for Human Approval Control Panel
        from ..models.approval_request import ApprovalRequest
        app_record = ApprovalRequest(
            approval_id=req_id,
            request_type="address_change",
            employee="🚚 Delivery Employee",
            customer_id=customer_id or record.customer_id or 1,
            shipment_id=record.id,
            reason=req.reason or "Customer requested address update",
            requested_action=f"Change delivery address for {record.shipment_id} to: {req.new_address}",
            status="Pending Approval",
            priority="Low"
        )
        db.add(app_record)
        audit = AuditLog(
            customer_id=customer_id or record.customer_id,
            action="Delivery Address Change Request",
            entity_type="Shipment",
            entity_id=record.shipment_id,
            result="Waiting for approval",
            details={
                "delivery_employee": "🚚 Delivery Employee",
                "request_id": req_id,
                "requested_address": req.new_address,
                "reason": req.reason,
                "policy_flag": "HUMAN_APPROVAL_REQUIRED"
            }
        )
        
        # Also create ticket for support team review
        t = Ticket(
            ticket_id=f"LGT-{random.randint(1000, 9999)}",
            customer_id=customer_id or record.customer_id or 1,
            shipment_id=record.id,
            issue_type="Address Change Request",
            issue=f"Address Change Request for {record.shipment_id} to: {req.new_address}. Waiting for human approval.",
            priority="Medium",
            status="Waiting for approval",
            assigned_to="Delivery Operations Team"
        )
        db.add(t)
        db.add(audit)
        db.commit()

        return AddressChangeResponse(
            request_id=req_id,
            shipment_id=record.shipment_id,
            status="waiting_for_approval",
            requires_human_approval=True,
            message=f"Delivery address change request for shipment {record.shipment_id} submitted. Waiting for human approval."
        )

    @classmethod
    def create_support_request(
        cls,
        req: DeliverySupportRequest,
        db: Session,
        customer_id: Optional[int] = None
    ) -> DeliverySupportResponse:
        shipment_clean = req.shipment_id.strip().upper()
        record = cls.get_delivery_record(shipment_clean, db)
        req_id = cls._generate_req_id()

        t = Ticket(
            ticket_id=f"LGT-{random.randint(1000, 9999)}",
            customer_id=customer_id or record.customer_id or 1,
            shipment_id=record.id,
            issue_type=req.issue_type,
            issue=f"Delivery Support Request: {req.message}",
            priority="Medium",
            status="In Progress",
            assigned_to="Delivery Support Desk"
        )
        db.add(t)

        audit = AuditLog(
            customer_id=customer_id or record.customer_id,
            action="Create Delivery Support Request",
            entity_type="Shipment",
            entity_id=record.shipment_id,
            result="Created",
            details={
                "delivery_employee": "🚚 Delivery Employee",
                "request_id": req_id,
                "issue_type": req.issue_type,
                "message": req.message
            }
        )
        db.add(audit)
        db.commit()

        return DeliverySupportResponse(
            request_id=req_id,
            shipment_id=record.shipment_id,
            status="created",
            message=f"Delivery support request created successfully with ID {req_id}."
        )
