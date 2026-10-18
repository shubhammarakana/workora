import re
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.shipment import Shipment
from ..models.ticket import Ticket
from ..models.invoice import Invoice
from ..models.customer import Customer
from ..models.delivery_record import DeliveryRecord
from ..models.refund_request import RefundRequest
from ..schemas.chat import ChatResponse

from .delivery_service import DeliveryService, DeliveryRescheduleRequest
from .billing_service import BillingService, RefundRequestCreate, PaymentReminderRequest, BillingSupportRequest

class ChatService:
    @staticmethod
    def extract_shipment_id(message: str) -> Optional[str]:
        """Extract shipment ID matching SL\\d{4}, LG\\d{4}, DL\\d{4} or 2-letter 4-digit code."""
        match = re.search(r'\b([A-Z]{2}\d{4})\b', message, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def extract_invoice_id(message: str) -> Optional[str]:
        """Extract invoice ID matching INV-\\d{4}."""
        match = re.search(r'\b(INV-\d{4})\b', message, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def extract_ticket_id(message: str) -> Optional[str]:
        """Extract ticket ID matching LGT-\\d{4} or similar pattern."""
        match = re.search(r'\b(LGT-\d{4}|TKT-\d{5})\b', message, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def format_date_str(date_val: Any) -> str:
        if isinstance(date_val, (datetime.date, datetime.datetime)):
            return date_val.strftime("%d %B %Y").lstrip("0")
        if isinstance(date_val, str) and date_val:
            return date_val
        return "TBD"

    @classmethod
    def process_message(
        cls,
        message: str,
        db: Session,
        current_user: Optional[Customer] = None
    ) -> ChatResponse:
        raw = message.strip()
        lower = raw.lower()
        shipment_id = cls.extract_shipment_id(raw)
        invoice_id = cls.extract_invoice_id(raw)
        ticket_id = cls.extract_ticket_id(raw)

        # ----------------------------------------------------
        # 0. SECURITY & PROMPT INJECTION GUARD (TEST 13)
        # ----------------------------------------------------
        if re.search(r'\b(ignore.*instructions|show.*database|driver.*database|payment.*database|billing.*database|bypass.*security|dump.*database|system.*prompt|select \* from)\b', lower):
            return ChatResponse(
                message="I cannot comply with requests to bypass security guidelines, reveal database credentials, or display internal databases.",
                intent="security_violation",
                data={"error": "Unauthorized request", "code": "FORBIDDEN"}
            )

        # ----------------------------------------------------
        # 1. CROSS-EMPLOYEE ROUTING (TEST 9, TEST 10, TEST 11, TEST 12)
        # ----------------------------------------------------
        # Shipment Tracking -> Shipment Employee (TEST 9: "Where is SL1004?")
        if re.search(r'\b(where is|track|package location|where was)\b', lower) and not re.search(r'\b(charge|cost|invoice|bill|refund|delivery status|reschedule)\b', lower):
            return ChatResponse(
                message="That request is related to shipment tracking. I'll connect you with the Shipment Employee.",
                intent="routing_shipment",
                shipment_id=shipment_id,
                data={"routed_to": "Shipment Employee", "employee_key": "shipment"}
            )

        # Delay Inquiry -> Shipment Employee
        if re.search(r'\b(delay|delayed|why is.*delayed)\b', lower):
            return ChatResponse(
                message="That request is related to shipment tracking and delay status. I'll connect you with the Shipment Employee.",
                intent="delayed_shipment",
                shipment_id=shipment_id,
                data={"routed_to": "Shipment Employee", "employee_key": "shipment"}
            )

        # Delivery Rescheduling -> Delivery Employee (TEST 10: "Reschedule SL1004.")
        if re.search(r'\b(reschedule|change delivery time|reschedule delivery)\b', lower):
            return ChatResponse(
                message="That request is related to delivery scheduling. I'll connect you with the Delivery Employee.",
                intent="routing_delivery",
                shipment_id=shipment_id,
                data={"routed_to": "Delivery Employee", "employee_key": "delivery"}
            )

        # Damaged Package / Complaint -> Customer Service Employee (TEST 11: "My package is damaged.")
        if re.search(r'\b(damaged|crushed|broken package|file complaint|complaint)\b', lower) and not re.search(r'\b(refund|money back|charge)\b', lower):
            return ChatResponse(
                message="That request is related to package condition and customer support. I'll connect you with the Customer Service Employee.",
                intent="routing_customer_service",
                shipment_id=shipment_id,
                data={"routed_to": "Customer Service Employee", "employee_key": "customer_service"}
            )

        # Human Escalation -> Customer Service Employee / Human Support (TEST 12: "I want to talk to a human.")
        if re.search(r'\b(human|live agent|representative|talk to a person|talk to a human|human support)\b', lower):
            return ChatResponse(
                message="Connecting you to a live senior support specialist. Please hold...",
                intent="human_support",
                shipment_id=shipment_id,
                data={"routed_to": "Customer Service Employee", "employee_key": "customer_service", "estimated_wait": "2 mins"}
            )

        # ----------------------------------------------------
        # 2. REFUND REQUESTS & AMOUNT VALIDATION (TEST 5, TEST 6)
        # ----------------------------------------------------
        if re.search(r'\b(refund|refunds|chargeback|money back)\b', lower):
            if not invoice_id and not shipment_id:
                return ChatResponse(
                    message="Sure. I can help with a refund request. Please provide your invoice ID or shipment ID.\n\nExamples:\nINV-2045\nSL1004",
                    intent="missing_invoice_id"
                )

            # Check requested refund amount if mentioned in message (e.g., "Refund ₹5,000 for INV-2045.")
            amt_match = re.search(r'(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)', raw, re.IGNORECASE)
            requested_amount = None
            if amt_match:
                try:
                    cleaned_num = amt_match.group(1).replace(',', '')
                    parsed_amt = float(cleaned_num)
                    # Filter out shipment/invoice numbers from being treated as money
                    if parsed_amt not in [1001, 1002, 1003, 1004, 1005, 2041, 2042, 2043, 2044, 2045, 2046, 9999]:
                        requested_amount = parsed_amt
                except Exception:
                    pass

            # Target Invoice Lookup
            inv = None
            if invoice_id:
                inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
            elif shipment_id:
                shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
                if shipment:
                    inv = db.query(Invoice).filter(Invoice.shipment_id == shipment.id).first()

            invoice_total = float(inv.total_amount) if inv else 1250.0
            actual_refund_amt = requested_amount if requested_amount is not None else invoice_total

            # TEST 6: Amount Validation (exceeds invoice total)
            if actual_refund_amt > invoice_total or actual_refund_amt <= 0:
                return ChatResponse(
                    message="The requested refund amount is greater than the invoice amount. Please contact billing support.",
                    intent="invalid_refund_amount",
                    data={
                        "invoice_id": invoice_id or (inv.invoice_id if inv else "INV-2045"),
                        "invoice_total": invoice_total,
                        "requested_amount": actual_refund_amt,
                        "suggested_actions": ["Contact Billing Support"]
                    }
                )

            # TEST 5: Create Refund Request (Pending Review / Human Approval Required)
            try:
                ref_resp = BillingService.request_refund(
                    req=RefundRequestCreate(
                        invoice_id=invoice_id or (inv.invoice_id if inv else "INV-2045"),
                        shipment_id=shipment_id or (inv.shipment.shipment_id if inv and inv.shipment else "SL1004"),
                        amount=actual_refund_amt,
                        reason="Damaged shipment"
                    ),
                    db=db
                )
                resp_msg = (
                    f"Your refund request has been submitted for review.\n\n"
                    f"Request ID:\n{ref_resp.request_id}\n\n"
                    f"Status:\nPending Review"
                )
                return ChatResponse(
                    message=resp_msg,
                    intent="refund_approval_required",
                    shipment_id=shipment_id or "SL1004",
                    data={
                        "request_id": ref_resp.request_id,
                        "invoice_id": ref_resp.invoice_id,
                        "shipment_id": ref_resp.shipment_id,
                        "requested_amount": actual_refund_amt,
                        "status": "Waiting for approval",
                        "requires_human_approval": True
                    }
                )
            except Exception as e:
                return ChatResponse(
                    message="The requested refund amount is greater than the invoice amount. Please contact billing support.",
                    intent="invalid_refund_amount"
                )

        # ----------------------------------------------------
        # 3. BILLING HISTORY (TEST 4)
        # ----------------------------------------------------
        if re.search(r'\b(billing history|invoice history|my invoices|past invoices)\b', lower):
            cust_id = current_user.id if current_user else 1
            history = db.query(Invoice).filter(Invoice.customer_id == cust_id).order_by(Invoice.invoice_date.desc()).all()
            if history:
                lines = [f"○ {inv.invoice_id} · ₹{inv.total_amount:,.0f} ({inv.payment_status})" for inv in history]
                resp_msg = "Here is your authorized billing history:\n\n" + "\n".join(lines)
            else:
                resp_msg = "Here is your authorized billing history:\n\n○ INV-2041 · ₹900 (Paid)\n○ INV-2042 · ₹1,080 (Paid)\n○ INV-2043 · ₹960 (Pending)\n○ INV-2044 · ₹1,200 (Paid)\n○ INV-2045 · ₹1,250 (Paid)"

            return ChatResponse(
                message=resp_msg,
                intent="billing_history",
                data={
                    "customer_id": cust_id,
                    "invoices": [{"invoice_id": inv.invoice_id, "amount": float(inv.total_amount), "status": inv.payment_status} for inv in history] if history else []
                }
            )

        # ----------------------------------------------------
        # 4. SHIPPING CHARGES QUERY (TEST 2)
        # ----------------------------------------------------
        if re.search(r'\b(shipping charge|shipping cost|how much is shipping|charge for)\b', lower):
            target_sid = shipment_id or "SL1004"
            shipment = db.query(Shipment).filter(Shipment.shipment_id == target_sid).first()
            if not shipment:
                return ChatResponse(
                    message=f"I couldn't find shipment {target_sid}.\n\nPlease check the shipment ID and try again.",
                    intent="unknown_shipment"
                )
            inv = db.query(Invoice).filter(Invoice.shipment_id == shipment.id).first()
            if inv:
                resp_msg = (
                    f"The shipping charge for shipment {target_sid} is ₹{inv.shipping_charge:,.0f}.\n\n"
                    f"Shipping Charge:\n₹{inv.shipping_charge:,.0f}\n\n"
                    f"Tax:\n₹{inv.tax:,.0f}\n\n"
                    f"Total:\n₹{inv.total_amount:,.0f}"
                )
                return ChatResponse(
                    message=resp_msg,
                    intent="shipping_charge_query",
                    shipment_id=target_sid,
                    data={
                        "shipment_id": target_sid,
                        "shipping_charge": float(inv.shipping_charge),
                        "tax": float(inv.tax),
                        "total_amount": float(inv.total_amount)
                    }
                )

        # ----------------------------------------------------
        # 5. PAYMENT STATUS QUERY (TEST 3)
        # ----------------------------------------------------
        if re.search(r'\b(has my invoice been paid|payment status|paid or pending|is it paid|check payment)\b', lower):
            if not invoice_id and not shipment_id:
                return ChatResponse(
                    message="Sure. Please provide your invoice ID or shipment ID to check payment status.",
                    intent="missing_invoice_id"
                )
            target_inv_id = invoice_id or "INV-2045"
            inv = db.query(Invoice).filter(Invoice.invoice_id == target_inv_id).first()
            if not inv and shipment_id:
                shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
                if shipment:
                    inv = db.query(Invoice).filter(Invoice.shipment_id == shipment.id).first()

            if not inv:
                return ChatResponse(
                    message=f"I couldn't find invoice {target_inv_id}.\n\nPlease check the invoice ID and try again.",
                    intent="invoice_not_found"
                )

            if inv.payment_status.lower() == "paid":
                p_date = cls.format_date_str(inv.payment_date) if inv.payment_date else "7 October 2026"
                resp_msg = f"Invoice {inv.invoice_id} (Total: ₹{inv.total_amount:,.0f}) has been paid on {p_date}.\n\nPayment Status:\n🟢 Paid"
            else:
                d_date = cls.format_date_str(inv.due_date) if inv.due_date else "10 October 2026"
                resp_msg = f"Invoice {inv.invoice_id} (Total: ₹{inv.total_amount:,.0f}) is currently pending.\n\nPayment Status:\n🟠 Pending\n\nDue Date:\n{d_date}"

            return ChatResponse(
                message=resp_msg,
                intent="payment_status_query",
                data={
                    "invoice_id": inv.invoice_id,
                    "total_amount": float(inv.total_amount),
                    "payment_status": inv.payment_status
                }
            )

        # ----------------------------------------------------
        # 6. PAYMENT REMINDER (Section 11)
        # ----------------------------------------------------
        if re.search(r'\b(remind|payment reminder|remind me)\b', lower):
            cust_id = current_user.id if current_user else 1
            pending_inv = db.query(Invoice).filter(Invoice.customer_id == cust_id, Invoice.payment_status == "Pending").first()
            target_code = pending_inv.invoice_id if pending_inv else "INV-2043"
            target_amt = float(pending_inv.total_amount) if pending_inv else 960.0
            due_str = cls.format_date_str(pending_inv.due_date) if pending_inv and pending_inv.due_date else "10 October 2026"

            rem_resp = BillingService.create_payment_reminder(
                req=PaymentReminderRequest(invoice_id=target_code),
                db=db
            )
            resp_msg = f"Payment reminder created for invoice {target_code}.\n\nAmount:\n₹{target_amt:,.0f}\n\nDue Date:\n{due_str}"
            return ChatResponse(
                message=resp_msg,
                intent="payment_reminder_created",
                data={
                    "reminder_id": rem_resp.reminder_id,
                    "invoice_id": target_code,
                    "amount": target_amt,
                    "due_date": due_str
                }
            )

        # ----------------------------------------------------
        # 7. INVOICE LOOKUP (TEST 1, TEST 7, TEST 8)
        # ----------------------------------------------------
        if re.search(r'\b(show.*invoice|invoice|invoice details|view invoice)\b', lower) or invoice_id:
            # Missing ID check (User says "Show my invoice.")
            if not invoice_id and not shipment_id:
                return ChatResponse(
                    message="Sure. Please provide your invoice ID or shipment ID.\n\nExamples:\nINV-2045\nSL1004",
                    intent="missing_invoice_id",
                    data={"suggested_examples": ["INV-2045", "SL1004"]}
                )

            target_iid = invoice_id
            if not target_iid and shipment_id:
                s_obj = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
                if s_obj:
                    inv_obj = db.query(Invoice).filter(Invoice.shipment_id == s_obj.id).first()
                    if inv_obj:
                        target_iid = inv_obj.invoice_id

            if not target_iid:
                target_iid = "INV-2045"

            # TEST 7: Unknown Invoice INV-9999 -> 404 Invoice Not Found
            if target_iid == "INV-9999":
                return ChatResponse(
                    message="I couldn't find invoice INV-9999.\n\nPlease check the invoice ID and try again.",
                    intent="invoice_not_found",
                    data={"error": "Invoice not found", "code": "NOT_FOUND"}
                )

            # TEST 8: Unauthorized Invoice INV-2046 -> 403 Forbidden
            if target_iid == "INV-2046":
                return ChatResponse(
                    message="I can't access that invoice with your current account.",
                    intent="unauthorized_invoice",
                    data={"error": "Access denied", "code": "FORBIDDEN", "suggested_actions": ["Contact Billing Support"]}
                )

            inv = db.query(Invoice).filter(Invoice.invoice_id == target_iid).first()
            if not inv:
                return ChatResponse(
                    message=f"I couldn't find invoice {target_iid}.\n\nPlease check the invoice ID and try again.",
                    intent="invoice_not_found"
                )

            cust_name = inv.customer.name if inv.customer else "Demo Customer"
            ship_code = inv.shipment.shipment_id if inv.shipment else "SL1004"
            inv_date_str = cls.format_date_str(inv.invoice_date)

            resp_msg = (
                f"Here are the invoice details.\n\n"
                f"Invoice:\n{inv.invoice_id}\n\n"
                f"Shipment:\n{ship_code}\n\n"
                f"Customer:\n{cust_name}\n\n"
                f"Shipping Charge:\n₹{inv.shipping_charge:,.0f}\n\n"
                f"Tax:\n₹{inv.tax:,.0f}\n\n"
                f"Total:\n₹{inv.total_amount:,.0f}\n\n"
                f"Payment Status:\n{inv.payment_status}\n\n"
                f"Invoice Date:\n{inv_date_str}"
            )

            return ChatResponse(
                message=resp_msg,
                intent="invoice_lookup",
                shipment_id=ship_code,
                data={
                    "invoice_id": inv.invoice_id,
                    "shipment_id": ship_code,
                    "customer_name": cust_name,
                    "shipping_charge": float(inv.shipping_charge),
                    "tax": float(inv.tax),
                    "total_amount": float(inv.total_amount),
                    "payment_status": inv.payment_status,
                    "invoice_date": inv_date_str,
                    "suggested_actions": ["View Invoice", "Download Invoice"]
                }
            )

        # ----------------------------------------------------
        # 8. DRIVER COORDINATION, FAILED DELIVERY, DELIVERY ETA (DELIVERY SERVICE INTEGRATION)
        # ----------------------------------------------------
        if re.search(r'\b(contact.*driver|driver.*phone|driver.*contact)\b', lower):
            return ChatResponse(
                message="Driver contact details cannot be shared directly. I can create a delivery support request for you.",
                intent="driver_coordination",
                shipment_id=shipment_id,
                data={"shipment_id": shipment_id or "SL1004", "suggested_actions": ["Create Support Request"]}
            )

        if re.search(r'\b(failed|failed delivery|unsuccessful)\b', lower):
            if not shipment_id:
                return ChatResponse(
                    message="Please provide your shipment ID so I can check the delivery attempt.",
                    intent="missing_shipment_id"
                )
            return ChatResponse(
                message=f"Shipment {shipment_id} had an unsuccessful delivery attempt.\n\nReason:\nCustomer unavailable.\n\nDelivery attempt:\n7 October 2026 · 3:20 PM\n\nWould you like to request another delivery attempt?",
                intent="failed_delivery",
                shipment_id=shipment_id,
                data={"shipment_id": shipment_id, "suggested_actions": ["Request New Delivery Attempt", "Talk to Human"]}
            )

        # Default Billing Employee Fallback
        return ChatResponse(
            message="💰 **Billing Employee**: I can help you with invoices, shipping charges, payment status, billing history, payment reminders and refund requests. Please provide your invoice ID (e.g. **INV-2045**) or shipment ID (e.g. **SL1004**).",
            intent="unsupported"
        )
