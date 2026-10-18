import random
import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.invoice import Invoice
from ..models.shipment import Shipment
from ..models.customer import Customer
from ..models.refund_request import RefundRequest
from ..models.ticket import Ticket
from ..models.audit_log import AuditLog

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

class BillingService:
    @staticmethod
    def _generate_ref_id() -> str:
        return f"REF-{random.randint(10000, 99999)}"

    @staticmethod
    def _generate_rem_id() -> str:
        return f"REM-{random.randint(10000, 99999)}"

    @classmethod
    def _format_invoice(cls, inv: Invoice) -> InvoiceOut:
        shipment_code = inv.shipment.shipment_id if inv.shipment else (str(inv.shipment_id) if inv.shipment_id else None)
        cust_name = inv.customer.name if inv.customer else "Demo Customer"
        return InvoiceOut(
            invoice_id=inv.invoice_id,
            customer_id=inv.customer_id,
            shipment_id=shipment_code,
            shipment_code=shipment_code,
            customer_name=cust_name,
            shipping_charge=float(inv.shipping_charge),
            tax=float(inv.tax),
            total_amount=float(inv.total_amount),
            payment_status=inv.payment_status,
            payment_date=inv.payment_date,
            invoice_date=inv.invoice_date,
            due_date=inv.due_date,
            currency=inv.currency or "INR",
            refund_status=inv.refund_status,
            refund_amount=float(inv.refund_amount) if inv.refund_amount is not None else None
        )

    @classmethod
    def get_invoice(
        cls,
        invoice_id: str,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> InvoiceOut:
        inv_clean = invoice_id.strip().upper()
        inv = db.query(Invoice).filter(Invoice.invoice_id == inv_clean).first()

        # TEST 7: 404 Invoice Not Found
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"I couldn't find invoice {inv_clean}. Please check the invoice ID and try again.", "code": "INVOICE_NOT_FOUND"}
            )

        # TEST 8: Authorization check
        # In prototype mode, customer 1 (CUST001) owns INV-2041, INV-2043, INV-2045. INV-2046 belongs to CUST002.
        if current_user and inv.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "I can't access that invoice with your current account.", "code": "FORBIDDEN"}
            )

        return cls._format_invoice(inv)

    @classmethod
    def get_invoice_by_shipment(
        cls,
        shipment_id: str,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> InvoiceOut:
        s_clean = shipment_id.strip().upper()
        shipment = db.query(Shipment).filter(Shipment.shipment_id == s_clean).first()
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"I couldn't find shipment {s_clean}. Please check the shipment ID and try again.", "code": "SHIPMENT_NOT_FOUND"}
            )

        inv = db.query(Invoice).filter(Invoice.shipment_id == shipment.id).first()
        if not inv:
            # Fallback query by shipment relationship
            inv = db.query(Invoice).join(Shipment).filter(Shipment.shipment_id == s_clean).first()

        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"No invoice found for shipment {s_clean}.", "code": "INVOICE_NOT_FOUND"}
            )

        if current_user and inv.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "I can't access that invoice with your current account.", "code": "FORBIDDEN"}
            )

        return cls._format_invoice(inv)

    @classmethod
    def get_billing_history(
        cls,
        customer_id: str,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> BillingHistoryOut:
        cust_str = str(customer_id).strip()
        cust_obj = None
        if cust_str.isdigit():
            cust_obj = db.query(Customer).filter(Customer.id == int(cust_str)).first()
        else:
            cust_obj = db.query(Customer).filter(Customer.customer_id == cust_str.upper()).first()

        target_cust = cust_obj.id if cust_obj else 1

        if current_user and getattr(current_user, "role", "customer").lower() != "admin":
            if current_user.id != target_cust:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "I can't access another customer's billing history.", "code": "FORBIDDEN"}
                )

        invoices = db.query(Invoice).filter(Invoice.customer_id == target_cust).order_by(Invoice.invoice_date.desc()).all()
        formatted = [cls._format_invoice(inv) for inv in invoices]
        return BillingHistoryOut(customer_id=customer_id, invoices=formatted)

    @classmethod
    def create_payment_reminder(
        cls,
        req: PaymentReminderRequest,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> PaymentReminderResponse:
        inv = None
        if req.invoice_id:
            inv = db.query(Invoice).filter(Invoice.invoice_id == req.invoice_id.strip().upper()).first()
        elif req.shipment_id:
            s_clean = req.shipment_id.strip().upper()
            shipment = db.query(Shipment).filter(Shipment.shipment_id == s_clean).first()
            if shipment:
                inv = db.query(Invoice).filter(Invoice.shipment_id == shipment.id).first()

        if not inv:
            # Pick first pending invoice for user
            cust_id = current_user.id if current_user else 1
            inv = db.query(Invoice).filter(Invoice.customer_id == cust_id, Invoice.payment_status == "Pending").first()

        if not inv:
            inv = db.query(Invoice).first()

        rem_id = cls._generate_rem_id()
        due_str = str(inv.due_date) if inv and inv.due_date else "10 October 2026"
        inv_code = inv.invoice_id if inv else "INV-2045"
        amt = float(inv.total_amount) if inv else 1250.0

        audit = AuditLog(
            customer_id=current_user.id if current_user else (inv.customer_id if inv else 1),
            action="Payment Reminder Request",
            entity_type="Invoice",
            entity_id=inv_code,
            result="Created",
            details={
                "billing_employee": "💰 Billing Employee",
                "reminder_id": rem_id,
                "amount": amt,
                "due_date": due_str
            }
        )
        db.add(audit)
        db.commit()

        return PaymentReminderResponse(
            reminder_id=rem_id,
            invoice_id=inv_code,
            amount=amt,
            due_date=due_str,
            status="Created",
            message=f"Payment reminder created for invoice {inv_code}."
        )

    @classmethod
    def request_refund(
        cls,
        req: RefundRequestCreate,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> RefundRequestOut:
        inv = None
        target_shipment = None

        if req.invoice_id:
            inv_clean = req.invoice_id.strip().upper()
            inv = db.query(Invoice).filter(Invoice.invoice_id == inv_clean).first()
        if not inv and req.shipment_id:
            s_clean = req.shipment_id.strip().upper()
            target_shipment = db.query(Shipment).filter(Shipment.shipment_id == s_clean).first()
            if target_shipment:
                inv = db.query(Invoice).filter(Invoice.shipment_id == target_shipment.id).first()

        if not inv and not target_shipment:
            # Check default demo invoice INV-2045 / SL1004
            inv = db.query(Invoice).filter(Invoice.invoice_id == "INV-2045").first()

        if not target_shipment and inv and inv.shipment:
            target_shipment = inv.shipment

        inv_code = inv.invoice_id if inv else "INV-2045"
        ship_code = target_shipment.shipment_id if target_shipment else "SL1004"
        invoice_total = float(inv.total_amount) if inv else 1250.0

        refund_amt = req.get_amount

        # TEST 6: Amount validation check (cannot exceed invoice total or be <= 0)
        if refund_amt <= 0 or refund_amt > invoice_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "The requested refund amount is greater than the invoice amount. Please contact billing support.",
                    "code": "INVALID_REFUND_AMOUNT",
                    "max_allowed": invoice_total,
                    "requested": refund_amt
                }
            )

        ref_id = cls._generate_ref_id()

        # Create RefundRequest record in database
        refund_record = RefundRequest(
            refund_id=ref_id,
            customer_id=current_user.id if current_user else (inv.customer_id if inv else 1),
            shipment_id=target_shipment.id if target_shipment else 1,
            invoice_id=inv.id if inv else None,
            amount=refund_amt,
            reason=req.reason,
            status="Pending Approval"
        )
        db.add(refund_record)

        # Create corresponding ApprovalRequest for Human Approval Control Panel
        from ..models.approval_request import ApprovalRequest
        app_record = ApprovalRequest(
            approval_id=ref_id,
            request_type="refund",
            employee="💰 Billing Employee",
            customer_id=current_user.id if current_user else (inv.customer_id if inv else 1),
            shipment_id=target_shipment.id if target_shipment else 1,
            invoice_id=inv.id if inv else None,
            amount=refund_amt,
            reason=req.reason,
            requested_action=f"Refund ₹{refund_amt:,.0f}",
            status="Pending Approval",
            priority="High" if refund_amt >= 5000 else "Medium"
        )
        db.add(app_record)

        # Audit Log
        audit = AuditLog(
            customer_id=current_user.id if current_user else (inv.customer_id if inv else 1),
            action="Refund Request Submitted",
            entity_type="Invoice",
            entity_id=inv_code,
            result="Pending Human Approval",
            details={
                "billing_employee": "💰 Billing Employee",
                "request_id": ref_id,
                "requested_amount": refund_amt,
                "invoice_total": invoice_total,
                "reason": req.reason,
                "policy_flag": "HUMAN_APPROVAL_REQUIRED"
            }
        )
        db.add(audit)
        db.commit()

        return RefundRequestOut(
            request_id=ref_id,
            invoice_id=inv_code,
            shipment_id=ship_code,
            requested_amount=refund_amt,
            reason=req.reason,
            status="Pending Review",
            requires_human_approval=True,
            message="Your refund request has been submitted for review."
        )

    @classmethod
    def get_refund_request(cls, request_id: str, db: Session) -> RefundRequestOut:
        ref_clean = request_id.strip().upper()
        refund = db.query(RefundRequest).filter(RefundRequest.refund_id == ref_clean).first()
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Refund request {ref_clean} not found.", "code": "REFUND_NOT_FOUND"}
            )
        inv_code = refund.invoice.invoice_id if refund.invoice else "INV-2045"
        ship_code = refund.shipment.shipment_id if refund.shipment else "SL1004"
        return RefundRequestOut(
            request_id=refund.refund_id,
            invoice_id=inv_code,
            shipment_id=ship_code,
            requested_amount=float(refund.amount),
            reason=refund.reason,
            status=refund.status,
            requires_human_approval=True,
            message=f"Refund request {refund.refund_id} is currently {refund.status}."
        )

    @classmethod
    def create_support_request(
        cls,
        req: BillingSupportRequest,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> BillingSupportResponse:
        req_id = f"LGT-{random.randint(1000, 9999)}"
        t = Ticket(
            ticket_id=req_id,
            customer_id=current_user.id if current_user else 1,
            issue_type=req.issue_type,
            issue=f"Billing Support Request for {req.invoice_id or 'General'}: {req.message}",
            priority="Medium",
            status="In Progress",
            assigned_to="Billing Support Desk"
        )
        db.add(t)

        audit = AuditLog(
            customer_id=current_user.id if current_user else 1,
            action="Create Billing Support Request",
            entity_type="Invoice",
            entity_id=req.invoice_id or "GENERAL",
            result="Created",
            details={
                "billing_employee": "💰 Billing Employee",
                "request_id": req_id,
                "issue_type": req.issue_type,
                "message": req.message
            }
        )
        db.add(audit)
        db.commit()

        return BillingSupportResponse(
            request_id=req_id,
            invoice_id=req.invoice_id,
            status="Created",
            message=f"Billing support request created successfully with ticket ID {req_id}."
        )
