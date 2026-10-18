import random
import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.approval_request import ApprovalRequest
from ..models.refund_request import RefundRequest
from ..models.invoice import Invoice
from ..models.shipment import Shipment
from ..models.customer import Customer
from ..models.audit_log import AuditLog

from ..schemas.approval import (
    ApprovalCreate,
    ApprovalOut,
    ApprovalDecision,
    ApprovalStats
)

class ApprovalService:
    @staticmethod
    def _generate_approval_id() -> str:
        return f"APR-{random.randint(10000, 99999)}"

    @classmethod
    def _format_approval(cls, app: ApprovalRequest) -> ApprovalOut:
        cust_name = app.customer.name if app.customer else "Demo Customer"
        ship_code = app.shipment.shipment_id if app.shipment else (app.shipment_id if isinstance(app.shipment_id, str) else None)
        inv_code = app.invoice.invoice_id if app.invoice else (app.invoice_id if isinstance(app.invoice_id, str) else None)
        
        # Risk assessment rule
        amt = float(app.amount) if app.amount is not None else 0.0
        risk = "High" if amt >= 5000 or app.request_type in ["cancellation", "sensitive_billing"] else "Medium"
        if app.priority == "Critical":
            risk = "Critical"

        return ApprovalOut(
            approval_id=app.approval_id,
            request_type=app.request_type,
            employee=app.employee,
            customer_id=app.customer_id,
            customer_name=cust_name,
            shipment_id=ship_code or "SL1004",
            invoice_id=inv_code or "INV-2045",
            amount=amt if amt > 0 else None,
            reason=app.reason or "Sensitive action authorization required",
            requested_action=app.requested_action or f"{app.request_type.capitalize()} request authorization",
            status=app.status,
            priority=app.priority or "Medium",
            created_at=app.created_at,
            updated_at=app.updated_at,
            reviewed_by=app.reviewed_by,
            reviewed_at=app.reviewed_at,
            review_comment=app.review_comment,
            ai_recommendation="Approve",
            risk_level=risk
        )

    @classmethod
    def create_approval_request(
        cls,
        req: ApprovalCreate,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> ApprovalOut:
        app_id = cls._generate_approval_id()

        # Lookup customer, shipment, invoice
        cust_id = None
        if current_user:
            cust_id = current_user.id
        elif req.customer_id:
            c_str = str(req.customer_id).strip()
            if c_str.isdigit():
                cust_id = int(c_str)
            else:
                cust_obj = db.query(Customer).filter(Customer.customer_id == c_str.upper()).first()
                if cust_obj:
                    cust_id = cust_obj.id

        if not cust_id:
            cust_id = 1 # Fallback to default demo customer

        ship_obj = None
        if req.shipment_id:
            ship_obj = db.query(Shipment).filter(Shipment.shipment_id == req.shipment_id.strip().upper()).first()

        inv_obj = None
        if req.invoice_id:
            inv_obj = db.query(Invoice).filter(Invoice.invoice_id == req.invoice_id.strip().upper()).first()

        # Build requested_action string if not provided
        action_text = req.requested_action
        if not action_text:
            if req.request_type == "refund":
                action_text = f"Refund ₹{req.amount:,.0f}" if req.amount else "Process Refund Request"
            elif req.request_type == "address_change":
                action_text = f"Change Delivery Address for {req.shipment_id or 'SL1004'}"
            elif req.request_type == "cancellation":
                action_text = f"Cancel Shipment {req.shipment_id or 'SL1004'}"
            else:
                action_text = f"{req.request_type.capitalize()} authorization"

        app_record = ApprovalRequest(
            approval_id=app_id,
            request_type=req.request_type,
            employee=req.employee,
            customer_id=cust_id,
            shipment_id=ship_obj.id if ship_obj else None,
            invoice_id=inv_obj.id if inv_obj else None,
            amount=req.amount,
            reason=req.reason,
            requested_action=action_text,
            status="Pending Approval",
            priority=req.priority or ("High" if (req.amount and req.amount > 5000) else "Medium")
        )
        db.add(app_record)

        # Create Audit Log
        audit = AuditLog(
            customer_id=cust_id,
            action=f"Approval Request Created ({req.request_type})",
            entity_type="ApprovalRequest",
            entity_id=app_id,
            result="Pending Approval",
            details={
                "employee": req.employee,
                "amount": req.amount,
                "reason": req.reason,
                "policy_flag": "HUMAN_APPROVAL_REQUIRED"
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(app_record)

        return cls._format_approval(app_record)

    @classmethod
    def get_approvals(
        cls,
        db: Session,
        status_filter: Optional[str] = None
    ) -> List[ApprovalOut]:
        query = db.query(ApprovalRequest)
        if status_filter and status_filter.lower() != "all":
            query = query.filter(ApprovalRequest.status.ilike(f"%{status_filter}%"))
        
        records = query.order_by(ApprovalRequest.created_at.desc()).all()
        return [cls._format_approval(app) for app in records]

    @classmethod
    def get_approval_by_id(cls, approval_id: str, db: Session) -> ApprovalOut:
        clean_id = approval_id.strip().upper()
        app = db.query(ApprovalRequest).filter(ApprovalRequest.approval_id == clean_id).first()
        if not app:
            # Check if searched by refund_id or request_type
            app = db.query(ApprovalRequest).filter(ApprovalRequest.approval_id.contains(clean_id)).first()

        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Approval request {clean_id} not found.", "code": "APPROVAL_NOT_FOUND"}
            )
        return cls._format_approval(app)

    @classmethod
    def approve_request(
        cls,
        approval_id: str,
        db: Session,
        is_admin: bool = False,
        reviewer_name: str = "Authorized Admin",
        decision: Optional[ApprovalDecision] = None
    ) -> ApprovalOut:
        # SECURITY CHECK 1: Customers cannot approve sensitive actions
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Access denied: Standard customers cannot approve action requests. Authorized internal staff or admin role required.", "code": "FORBIDDEN"}
            )

        clean_id = approval_id.strip().upper()
        app = db.query(ApprovalRequest).filter(ApprovalRequest.approval_id == clean_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Approval request {clean_id} not found.", "code": "NOT_FOUND"}
            )

        # SECURITY CHECK 2: Double-approval or replay prevention
        if app.status != "Pending Approval":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": f"Approval request {clean_id} is already in state '{app.status}'. Duplicate approval rejected.", "code": "CONFLICT"}
            )

        # Update approval status
        app.status = "Approved"
        app.reviewed_by = reviewer_name
        app.reviewed_at = datetime.datetime.now()
        app.review_comment = decision.review_comment if (decision and decision.review_comment) else "Approved by human administrator"
        app.updated_at = datetime.datetime.now()

        # Execute authorized action based on request_type
        if app.request_type == "refund" and app.invoice_id:
            inv = db.query(Invoice).filter(Invoice.id == app.invoice_id).first()
            if inv:
                inv.refund_status = "Approved"
                inv.refund_amount = app.amount or inv.total_amount
            
            # Update associated RefundRequest record
            ref_req = db.query(RefundRequest).filter(RefundRequest.invoice_id == app.invoice_id).first()
            if ref_req:
                ref_req.status = "Approved"
                ref_req.approved_by = reviewer_name
                ref_req.approved_at = datetime.datetime.now()

        elif app.request_type == "cancellation" and app.shipment_id:
            ship = db.query(Shipment).filter(Shipment.id == app.shipment_id).first()
            if ship:
                ship.status = "Cancelled"

        # Record Audit Log
        audit = AuditLog(
            customer_id=app.customer_id or 1,
            action="Human Approval Granted",
            entity_type="ApprovalRequest",
            entity_id=clean_id,
            result="Approved & Executed",
            details={
                "reviewed_by": reviewer_name,
                "request_type": app.request_type,
                "amount": float(app.amount) if app.amount else None,
                "requested_action": app.requested_action
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(app)

        return cls._format_approval(app)

    @classmethod
    def reject_request(
        cls,
        approval_id: str,
        db: Session,
        is_admin: bool = False,
        reviewer_name: str = "Authorized Admin",
        decision: Optional[ApprovalDecision] = None
    ) -> ApprovalOut:
        # SECURITY CHECK 1: Customers cannot reject/approve sensitive actions
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Access denied: Standard customers cannot perform review actions. Authorized internal staff required.", "code": "FORBIDDEN"}
            )

        clean_id = approval_id.strip().upper()
        app = db.query(ApprovalRequest).filter(ApprovalRequest.approval_id == clean_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Approval request {clean_id} not found.", "code": "NOT_FOUND"}
            )

        if app.status != "Pending Approval":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": f"Approval request {clean_id} is already in state '{app.status}'. Rejection rejected.", "code": "CONFLICT"}
            )

        rej_reason = (decision.reason if decision and decision.reason else None) or (decision.review_comment if decision and decision.review_comment else "Refund exceeds policy limit.")

        app.status = "Rejected"
        app.reviewed_by = reviewer_name
        app.reviewed_at = datetime.datetime.now()
        app.review_comment = rej_reason
        app.updated_at = datetime.datetime.now()

        # Update associated RefundRequest record to Rejected
        if app.request_type == "refund" and app.invoice_id:
            inv = db.query(Invoice).filter(Invoice.id == app.invoice_id).first()
            if inv:
                inv.refund_status = "Rejected"
            ref_req = db.query(RefundRequest).filter(RefundRequest.invoice_id == app.invoice_id).first()
            if ref_req:
                ref_req.status = "Rejected"

        # Record Audit Log
        audit = AuditLog(
            customer_id=app.customer_id or 1,
            action="Human Approval Rejected",
            entity_type="ApprovalRequest",
            entity_id=clean_id,
            result="Rejected & Cancelled",
            details={
                "reviewed_by": reviewer_name,
                "request_type": app.request_type,
                "rejection_reason": rej_reason
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(app)

        return cls._format_approval(app)

    @classmethod
    def get_stats(cls, db: Session) -> ApprovalStats:
        pending_count = db.query(ApprovalRequest).filter(ApprovalRequest.status == "Pending Approval").count()
        approved_count = db.query(ApprovalRequest).filter(ApprovalRequest.status == "Approved").count()
        rejected_count = db.query(ApprovalRequest).filter(ApprovalRequest.status == "Rejected").count()

        return ApprovalStats(
            pending_approvals=pending_count or 12,
            approved_today=approved_count or 18,
            rejected_today=rejected_count or 3,
            avg_approval_time_min=8.0,
            label="Demo Data"
        )
