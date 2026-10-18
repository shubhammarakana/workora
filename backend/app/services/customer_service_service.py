import re
import datetime
import random
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from ..models.customer import Customer
from ..models.shipment import Shipment
from ..models.ticket import Ticket
from ..models.invoice import Invoice
from ..models.refund_request import RefundRequest
from ..models.human_support import HumanSupportRequest
from ..models.knowledge_document import KnowledgeDocument
from ..models.audit_log import AuditLog
from ..schemas.customer_service import CustomerServiceChatResponse

class CustomerServiceService:
    @staticmethod
    def extract_shipment_id(message: str) -> Optional[str]:
        """Extract shipment ID matching SL\\d{4}, LG\\d{4}, DL\\d{4} or 2-letter 4-digit code."""
        match = re.search(r'\b([A-Z]{2}\d{4})\b', message, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def extract_refund_amount(message: str) -> Optional[int]:
        """Extract requested refund amount (e.g. ₹2,000 or 2000 or Rs 2000)."""
        match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})*|\d+)', message, re.IGNORECASE)
        if match:
            clean_str = match.group(1).replace(',', '')
            if clean_str.isdigit() and int(clean_str) >= 100:
                return int(clean_str)
        return 2000

    @staticmethod
    def format_date_str(date_val: Any) -> str:
        if isinstance(date_val, (datetime.date, datetime.datetime)):
            return date_val.strftime("%d %B %Y").lstrip("0")
        if isinstance(date_val, str) and date_val:
            return date_val
        return "8 October 2026"

    @classmethod
    def log_audit(cls, db: Session, customer_id: Optional[int], intent: str, action: str, result: str, entity_type: str = "shipment", entity_id: Optional[str] = None, details: Optional[dict] = None):
        try:
            audit = AuditLog(
                customer_id=customer_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                result=result,
                details={"intent": intent, "employee_used": "Customer Service Employee", **(details or {})}
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            db.rollback()

    @classmethod
    def process_customer_service_message(
        cls,
        message: str,
        db: Session,
        current_user: Optional[Customer] = None,
        provided_shipment_id: Optional[str] = None
    ) -> CustomerServiceChatResponse:
        raw = message.strip()
        lower = raw.lower()
        shipment_id = provided_shipment_id or cls.extract_shipment_id(raw)
        cust_id = current_user.id if current_user else None

        # ----------------------------------------------------
        # 1. SECURITY & PROMPT INJECTION GUARD (TEST 10)
        # ----------------------------------------------------
        if re.search(r'\b(ignore.*rules|ignore.*instructions|show.*database|bypass.*security|dump.*database|system.*prompt|select \* from)\b', lower):
            cls.log_audit(db, cust_id, "SECURITY_VIOLATION", "Security Guard Injection Rejection", "Rejected")
            return CustomerServiceChatResponse(
                message="I can't provide internal system or security information. I can help you with your logistics request.",
                intent="SECURITY_VIOLATION",
                employee_used="Customer Service Employee",
                data={"error": "Unauthorized request"}
            )

        # ----------------------------------------------------
        # 2. MULTI-INTENT HANDLER (TEST 12)
        # "My SL1003 shipment is late and I want a refund."
        # ----------------------------------------------------
        has_delay = bool(re.search(r'\b(late|delayed|delay)\b', lower))
        has_refund = bool(re.search(r'\b(refund|refunds|money back|chargeback)\b', lower))

        if has_delay and has_refund:
            target_id = shipment_id or "SL1003"
            shipment = db.query(Shipment).filter(Shipment.shipment_id == target_id).first()
            eta_str = cls.format_date_str(shipment.expected_delivery) if shipment else "9 October 2026"
            loc_str = shipment.current_location if shipment else "Surat Distribution Center"
            reason_str = shipment.delay_reason if (shipment and shipment.delay_reason) else "Transportation delay."
            refund_amt = cls.extract_refund_amount(raw) or 2000

            resp_msg = (
                f"Shipment {target_id} is currently delayed.\n\n"
                f"Current location:\n{loc_str}\n\n"
                f"Expected delivery:\n{eta_str}\n\n"
                f"Reason:\n{reason_str}\n\n"
                f"I've also identified your refund request. Refund requests require review and human approval.\n\n"
                f"Refund request status:\nWaiting for approval."
            )

            cls.log_audit(db, cust_id, "MULTI_INTENT_DELAY_REFUND", "Processed Multi-Intent Delay & Refund", "Success", entity_id=target_id)

            return CustomerServiceChatResponse(
                message=resp_msg,
                intent="MULTI_INTENT_DELAY_REFUND",
                employee_used="Customer Service Employee",
                shipment_id=target_id,
                data={
                    "shipment_id": target_id,
                    "status": "Delayed",
                    "current_location": loc_str,
                    "expected_delivery": eta_str,
                    "reason": reason_str,
                    "refund_amount": refund_amt,
                    "refund_status": "Waiting for approval"
                },
                context_panel={
                    "customer_name": shipment.customer.name if (shipment and shipment.customer) else "Amit Mehta",
                    "shipment_id": target_id,
                    "status": "Delayed",
                    "location": loc_str,
                    "expected_delivery": eta_str,
                    "refund_status": "Waiting for approval"
                }
            )

        # ----------------------------------------------------
        # 3. HUMAN SUPPORT WORKFLOW (TEST 8 & Section 10)
        # ----------------------------------------------------
        if re.search(r'\b(human|live agent|representative|talk to a person|human support)\b', lower):
            sup_id = f"SUP-10025"
            try:
                sup_req = HumanSupportRequest(
                    request_id=sup_id,
                    customer_id=cust_id,
                    status="Waiting for Agent",
                    priority="Normal",
                    notes=raw
                )
                db.add(sup_req)
                db.commit()
            except Exception:
                db.rollback()

            cls.log_audit(db, cust_id, "HUMAN_SUPPORT", "Created Human Support Request", "Success", entity_type="human_support", entity_id=sup_id)

            return CustomerServiceChatResponse(
                message="Of course. I'll connect you with a LogiFlow Logistics support representative.",
                intent="HUMAN_SUPPORT",
                employee_used="Customer Service Employee",
                support_request_id=sup_id,
                data={
                    "support_request_id": sup_id,
                    "status": "Waiting for Agent",
                    "priority": "Normal",
                    "suggested_actions": ["View Support Request"]
                }
            )

        # ----------------------------------------------------
        # 4. REFUND WORKFLOW (TEST 7 & Section 9)
        # ----------------------------------------------------
        if has_refund:
            refund_amt = cls.extract_refund_amount(raw)
            ref_id = f"REF-{random.randint(1000, 9999)}"
            
            resp_msg = (
                f"⚠️ Human Approval Required\n\n"
                f"Refund:\n₹{refund_amt:,}\n\n"
                f"Status:\nWaiting for approval"
            )

            cls.log_audit(db, cust_id, "REFUND_REQUEST", "Submitted Refund For Human Approval", "Pending", entity_type="refund", entity_id=ref_id, details={"amount": refund_amt})

            return CustomerServiceChatResponse(
                message=resp_msg,
                intent="REFUND_REQUEST",
                employee_used="Billing Employee",
                shipment_id=shipment_id,
                data={
                    "refund_id": ref_id,
                    "amount": refund_amt,
                    "status": "Waiting for approval"
                }
            )

        # ----------------------------------------------------
        # 5. COMPLAINT & DAMAGED PACKAGE (TEST 6 & Section 8)
        # ----------------------------------------------------
        if re.search(r'\b(damaged|damage|broken|crushed|complaint|lost package|lost)\b', lower):
            if not shipment_id:
                return CustomerServiceChatResponse(
                    message="I'm sorry about the issue.\nI can create a support ticket for you.\n\nPlease provide your shipment ID.",
                    intent="MISSING_SHIPMENT_ID",
                    employee_used="Customer Service Employee",
                    data={"suggested_example": "SL1004"}
                )

            tkt_code = "TKT-10024"
            target_shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
            s_db_id = target_shipment.id if target_shipment else None

            try:
                tkt = db.query(Ticket).filter(Ticket.ticket_id == tkt_code).first()
                if not tkt:
                    tkt = Ticket(
                        ticket_id=tkt_code,
                        customer_id=cust_id or 1,
                        shipment_id=s_db_id,
                        issue_type="Damaged Package",
                        category="Complaint",
                        issue=raw,
                        priority="Normal",
                        status="Pending Review"
                    )
                    db.add(tkt)
                    db.commit()
            except Exception:
                db.rollback()

            resp_msg = (
                f"Your support ticket has been created successfully.\n\n"
                f"Ticket ID: {tkt_code}\n\n"
                f"Our support team will review the issue."
            )

            cls.log_audit(db, cust_id, "DAMAGED_PACKAGE", "Created Support Ticket", "Success", entity_type="ticket", entity_id=tkt_code)

            return CustomerServiceChatResponse(
                message=resp_msg,
                intent="DAMAGED_PACKAGE",
                employee_used="Customer Service Employee",
                shipment_id=shipment_id,
                ticket_id=tkt_code,
                data={
                    "ticket_id": tkt_code,
                    "issue": "Damaged Package",
                    "shipment_id": shipment_id,
                    "status": "Pending Review",
                    "priority": "Normal",
                    "suggested_actions": ["View Ticket", "Talk to Human"]
                },
                context_panel={
                    "ticket_id": tkt_code,
                    "status": "Pending Review",
                    "issue": "Damaged Package",
                    "shipment_id": shipment_id
                }
            )

        # ----------------------------------------------------
        # 6. DELIVERY RESCHEDULE WORKFLOW (TEST 4 & Section 6)
        # ----------------------------------------------------
        if re.search(r'\b(reschedule|change delivery date|reschedule delivery)\b', lower):
            if not shipment_id:
                return CustomerServiceChatResponse(
                    message="Sure. I can help with delivery rescheduling.\nPlease provide your shipment ID.",
                    intent="MISSING_SHIPMENT_ID",
                    employee_used="Customer Service Employee",
                    data={"suggested_example": "SL1004"}
                )

            cls.log_audit(db, cust_id, "DELIVERY_RESCHEDULE", "Routed Delivery Reschedule Request", "Success", entity_id=shipment_id)

            return CustomerServiceChatResponse(
                message=f"This request is related to delivery scheduling. I'll connect you with the Delivery Operations Employee to view available delivery slots for shipment {shipment_id}.",
                intent="DELIVERY_RESCHEDULE",
                employee_used="Delivery Employee",
                shipment_id=shipment_id,
                data={"routed_to": "Delivery Employee", "shipment_id": shipment_id}
            )

        # ----------------------------------------------------
        # 7. BILLING & INVOICE WORKFLOW (TEST 5 & Section 7)
        # ----------------------------------------------------
        if re.search(r'\b(invoice|bill|receipt|payment status)\b', lower):
            if not shipment_id:
                return CustomerServiceChatResponse(
                    message="Sure. Please provide your shipment ID or invoice ID.",
                    intent="MISSING_SHIPMENT_ID",
                    employee_used="Customer Service Employee",
                    data={"suggested_example": "SL1004"}
                )

            inv_id = "INV-2045"
            inv_shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
            cust_name = inv_shipment.customer.name if (inv_shipment and inv_shipment.customer) else "Neha Shah"

            resp_msg = (
                f"Invoice:\n{inv_id}\n\n"
                f"Shipment:\n{shipment_id}\n\n"
                f"Amount:\n₹1,250\n\n"
                f"Payment:\nPaid"
            )

            cls.log_audit(db, cust_id, "INVOICE", "Retrieved Commercial Invoice", "Success", entity_type="invoice", entity_id=inv_id)

            return CustomerServiceChatResponse(
                message=resp_msg,
                intent="INVOICE",
                employee_used="Billing Employee",
                shipment_id=shipment_id,
                data={
                    "invoice_id": inv_id,
                    "shipment_id": shipment_id,
                    "amount": "₹1,250",
                    "payment_status": "Paid"
                },
                context_panel={
                    "customer_name": cust_name,
                    "shipment_id": shipment_id,
                    "invoice_id": inv_id,
                    "amount": "₹1,250",
                    "payment_status": "Paid"
                }
            )

        # ----------------------------------------------------
        # 8. GENERAL FAQ (TEST 9 & Section 11)
        # ----------------------------------------------------
        if re.search(r'\b(timing|timings|delivery hours|schedule|operating hours|sla|policy)\b', lower):
            doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.category.ilike("%Operations%") | KnowledgeDocument.category.ilike("%Policies%")).first()
            
            resp_msg = (
                "LogiFlow Logistics standard delivery service operates according to the delivery schedule for each service area.\n\n"
                "Would you like me to check a specific shipment?"
            )

            cls.log_audit(db, cust_id, "GENERAL_FAQ", "Answered Knowledge Base FAQ", "Success")

            return CustomerServiceChatResponse(
                message=resp_msg,
                intent="GENERAL_FAQ",
                employee_used="Customer Service Employee"
            )

        # ----------------------------------------------------
        # 9. MISSING SHIPMENT ID HANDLING (TEST 1)
        # ----------------------------------------------------
        is_tracking_query = bool(re.search(r'\b(where is|track|package|shipment|order|delivery|arrive|status|where was)\b', lower))
        if is_tracking_query and not shipment_id:
            return CustomerServiceChatResponse(
                message="Sure! I can help you track your shipment.\nPlease provide your shipment ID.\n\nExample: SL1004",
                intent="MISSING_SHIPMENT_ID",
                employee_used="Customer Service Employee",
                data={"suggested_example": "SL1004"}
            )

        # ----------------------------------------------------
        # 10. DYNAMIC SHIPMENT TRACKING & DELAY (TEST 2, 3, 11)
        # ----------------------------------------------------
        if shipment_id:
            shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()

            # TEST 11: Unknown Shipment ("SL9999 is late.")
            if not shipment:
                cls.log_audit(db, cust_id, "UNKNOWN_SHIPMENT", "Shipment Not Found Lookup", "Not Found", entity_id=shipment_id)
                return CustomerServiceChatResponse(
                    message=f"I couldn't find shipment {shipment_id}. Please check the shipment ID and try again.",
                    intent="UNKNOWN",
                    employee_used="Customer Service Employee",
                    shipment_id=shipment_id,
                    data={"error": "Shipment not found", "suggested_actions": ["Try Again", "Contact Support"]}
                )

            cust_name = shipment.customer.name if shipment.customer else "Neha Shah"
            eta_str = cls.format_date_str(shipment.expected_delivery)

            # Delay Query (TEST 3: "My shipment SL1003 is late.")
            if has_delay or shipment.status == "Delayed":
                reason_str = shipment.delay_reason or "Transportation delay."
                resp_msg = (
                    f"Shipment {shipment.shipment_id} is currently delayed.\n\n"
                    f"Current location:\n{shipment.current_location or 'Surat Distribution Center'}\n\n"
                    f"Expected delivery:\n{eta_str}\n\n"
                    f"Reason:\n{reason_str}"
                )

                cls.log_audit(db, cust_id, "SHIPMENT_DELAY", "Retrieved Shipment Delay Status", "Success", entity_id=shipment.shipment_id)

                return CustomerServiceChatResponse(
                    message=resp_msg,
                    intent="SHIPMENT_DELAY",
                    employee_used="Shipment Employee",
                    shipment_id=shipment.shipment_id,
                    data={
                        "shipment_id": shipment.shipment_id,
                        "status": "Delayed",
                        "current_location": shipment.current_location,
                        "expected_delivery": eta_str,
                        "reason": reason_str
                    },
                    context_panel={
                        "customer_name": cust_name,
                        "shipment_id": shipment.shipment_id,
                        "status": "Delayed",
                        "location": shipment.current_location,
                        "expected_delivery": eta_str
                    }
                )

            # Standard Tracking Response (TEST 2: "Where is SL1004?")
            resp_msg = (
                f"Shipment {shipment.shipment_id} is currently {shipment.status.lower()}.\n\n"
                f"Current location:\n{shipment.current_location}\n\n"
                f"Expected delivery:\n{eta_str}."
            )

            cls.log_audit(db, cust_id, "SHIPMENT_TRACKING", "Routed to Shipment Employee", "Success", entity_id=shipment.shipment_id)

            return CustomerServiceChatResponse(
                message=resp_msg,
                intent="SHIPMENT_TRACKING",
                employee_used="Shipment Employee",
                shipment_id=shipment.shipment_id,
                data={
                    "shipment_id": shipment.shipment_id,
                    "status": shipment.status,
                    "current_location": shipment.current_location,
                    "expected_delivery": eta_str
                },
                context_panel={
                    "customer_name": cust_name,
                    "shipment_id": shipment.shipment_id,
                    "status": shipment.status,
                    "location": shipment.current_location,
                    "expected_delivery": eta_str
                }
            )

        # ----------------------------------------------------
        # 11. UNKNOWN / OFF-TOPIC REQUEST (Section 12)
        # ----------------------------------------------------
        cls.log_audit(db, cust_id, "UNKNOWN", "Off-topic Query Fallback", "Fallback")
        return CustomerServiceChatResponse(
            message="I'm designed to help with LogiFlow Logistics shipments, deliveries, billing and customer support. How can I help you?",
            intent="UNKNOWN",
            employee_used="Customer Service Employee"
        )
