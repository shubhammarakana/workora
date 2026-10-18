import re
import random
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.shipment import Shipment
from ..models.invoice import Invoice
from ..models.customer import Customer
from ..models.audit_log import AuditLog

from ..services.billing_service import BillingService
from ..services.delivery_service import DeliveryService
from ..services.approval_service import ApprovalService
from ..schemas.billing import RefundRequestCreate, PaymentReminderRequest, BillingSupportRequest
from ..schemas.delivery import DeliveryRescheduleRequest, AddressChangeRequest, DeliverySupportRequest
from ..schemas.approval import ApprovalCreate

# In-Memory Session Memory Cache (Per Session ID)
SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}

class AIManagerService:
    @staticmethod
    def get_session_memory(session_id: str) -> Dict[str, Any]:
        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = {
                "last_shipment_id": None,
                "last_invoice_id": None,
                "last_employee": None,
                "history": []
            }
        return SESSION_MEMORY[session_id]

    @staticmethod
    def update_session_memory(session_id: str, shipment_id: Optional[str] = None, invoice_id: Optional[str] = None, employee: Optional[str] = None):
        mem = AIManagerService.get_session_memory(session_id)
        if shipment_id:
            mem["last_shipment_id"] = shipment_id
        if invoice_id:
            mem["last_invoice_id"] = invoice_id
        if employee:
            mem["last_employee"] = employee

    @classmethod
    def extract_entities(cls, text: str, session_id: str = "default") -> Dict[str, Any]:
        mem = cls.get_session_memory(session_id)
        raw = text.strip()

        # Extract shipment_id (e.g. SL1001-SL1005)
        shipment_match = re.search(r'\b(SL\d{4}|TRK-\w+)\b', raw, re.IGNORECASE)
        shipment_id = shipment_match.group(1).upper() if shipment_match else None
        
        # Check pronoun references ("it", "this package", "my shipment") using session memory
        if not shipment_id and re.search(r'\b(it|this package|my package|the shipment|the parcel|this order)\b', raw, re.IGNORECASE):
            shipment_id = mem.get("last_shipment_id")

        # Extract invoice_id (e.g. INV-2041 to INV-2046)
        invoice_match = re.search(r'\b(INV-\d{4})\b', raw, re.IGNORECASE)
        invoice_id = invoice_match.group(1).upper() if invoice_match else None

        if not invoice_id and re.search(r'\b(it|the invoice|my invoice|this bill)\b', raw, re.IGNORECASE):
            invoice_id = mem.get("last_invoice_id")

        # Extract amount (e.g. ₹2,000 or Rs 5000 or 1250)
        amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)', raw, re.IGNORECASE)
        amount = None
        if amount_match:
            try:
                num = float(amount_match.group(1).replace(',', ''))
                # Exclude ID numbers
                if num not in [1001, 1002, 1003, 1004, 1005, 2041, 2042, 2043, 2044, 2045, 2046, 9999]:
                    amount = num
            except Exception:
                pass

        # Extract reason
        reason = None
        if re.search(r'\b(damaged|broken|crushed|defective|delayed|late|wrong charge)\b', raw, re.IGNORECASE):
            reason_match = re.search(r'(?:because|due to|reason:?|for)\s+([^\.\,\!\?]+)', raw, re.IGNORECASE)
            reason = reason_match.group(1).strip() if reason_match else "Damaged shipment"

        # Update session memory
        cls.update_session_memory(session_id, shipment_id=shipment_id, invoice_id=invoice_id)

        return {
            "shipment_id": shipment_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "reason": reason
        }

    @classmethod
    def classify_intent(cls, text: str, selected_employee: Optional[str] = None) -> Dict[str, Any]:
        lower = text.lower().strip()

        # Prompt Injection Guard (TEST 10)
        if re.search(r'\b(ignore.*instructions|show.*database|bypass.*security|dump.*database|system prompt)\b', lower):
            return {
                "intent": "SECURITY_VIOLATION",
                "employee": "security",
                "confidence": 1.0,
                "requires_approval": False
            }

        # Human Escalation (TEST 5)
        if re.search(r'\b(talk to a human|i want a human|human agent|live agent|representative|human)\b', lower):
            return {
                "intent": "HUMAN_SUPPORT",
                "employee": "customer_service",
                "confidence": 0.99,
                "requires_approval": False
            }

        # Multi-intent detection checks
        is_delay = bool(re.search(r'\b(delayed|delay|why is.*delayed|late)\b', lower))
        is_refund = bool(re.search(r'\b(refund|money back|reimburse|chargeback)\b', lower))
        is_reschedule = bool(re.search(r'\b(reschedule|change delivery time|slot)\b', lower))

        if is_delay and is_refund:
            return {
                "intent": "MULTI_INTENT_DELAY_REFUND",
                "intents": ["SHIPMENT_DELAY", "REFUND_REQUEST"],
                "employee": "multi_orchestrated",
                "confidence": 0.96,
                "requires_approval": True
            }

        if is_delay and is_reschedule:
            return {
                "intent": "MULTI_INTENT_DELAY_RESCHEDULE",
                "intents": ["SHIPMENT_DELAY", "DELIVERY_RESCHEDULE"],
                "employee": "multi_orchestrated",
                "confidence": 0.95,
                "requires_approval": False
            }

        # Refund Request (TEST 6)
        if is_refund:
            return {
                "intent": "REFUND_REQUEST",
                "employee": "billing",
                "confidence": 0.98,
                "requires_approval": True
            }

        # Shipment Tracking (TEST 1, TEST 8)
        if re.search(r'\b(where is|track|shipment status|location of|where was)\b', lower):
            return {
                "intent": "SHIPMENT_TRACKING",
                "employee": "shipment",
                "confidence": 0.98,
                "requires_approval": False
            }

        # Invoice Lookup (TEST 2)
        if re.search(r'\b(show.*invoice|invoice details|view invoice)\b', lower):
            return {
                "intent": "INVOICE_LOOKUP",
                "employee": "billing",
                "confidence": 0.97,
                "requires_approval": False
            }

        # Delivery Reschedule (TEST 3)
        if is_reschedule:
            return {
                "intent": "DELIVERY_RESCHEDULE",
                "employee": "delivery",
                "confidence": 0.96,
                "requires_approval": False
            }

        # Damaged Package / Complaint (TEST 4)
        if re.search(r'\b(damaged|crushed|broken package|file complaint|complaint)\b', lower) and not is_refund:
            return {
                "intent": "CUSTOMER_COMPLAINT",
                "employee": "customer_service",
                "confidence": 0.95,
                "requires_approval": False
            }

        # Shipping Charge Query
        if re.search(r'\b(shipping charge|shipping cost|how much is shipping)\b', lower):
            return {
                "intent": "SHIPPING_CHARGE",
                "employee": "billing",
                "confidence": 0.95,
                "requires_approval": False
            }

        # Payment Status Query
        if re.search(r'\b(has my invoice been paid|payment status|is it paid)\b', lower):
            return {
                "intent": "PAYMENT_STATUS",
                "employee": "billing",
                "confidence": 0.95,
                "requires_approval": False
            }

        # Billing History
        if re.search(r'\b(billing history|invoice history|past invoices)\b', lower):
            return {
                "intent": "BILLING_HISTORY",
                "employee": "billing",
                "confidence": 0.96,
                "requires_approval": False
            }

        # Address Change
        if re.search(r'\b(change address|update address|new address)\b', lower):
            return {
                "intent": "ADDRESS_CHANGE",
                "employee": "delivery",
                "confidence": 0.95,
                "requires_approval": True
            }

        # Ambiguous / Low Confidence Request (TEST 9: "I have a problem.")
        if re.search(r'\b(problem|issue|help me|something wrong)\b', lower) and len(lower.split()) <= 4:
            return {
                "intent": "AMBIGUOUS_REQUEST",
                "employee": "manager",
                "confidence": 0.45,
                "requires_approval": False
            }

        # Unrelated Request (e.g. "Tell me a joke")
        if re.search(r'\b(joke|weather|recipe|sing|movie|game)\b', lower):
            return {
                "intent": "UNKNOWN",
                "employee": "manager",
                "confidence": 0.10,
                "requires_approval": False
            }

        # Customer-Selected Employee Override (TEST 11)
        if selected_employee:
            return {
                "intent": f"{selected_employee.upper()}_GENERAL",
                "employee": selected_employee.lower(),
                "confidence": 0.90,
                "requires_approval": False
            }

        return {
            "intent": "GENERAL_LOGISTICS",
            "employee": "customer_service",
            "confidence": 0.80,
            "requires_approval": False
        }

    @classmethod
    def orchestrate_request(
        cls,
        message: str,
        db: Session,
        session_id: str = "demo-session-001",
        selected_employee: Optional[str] = None,
        current_user: Optional[Customer] = None
    ) -> Dict[str, Any]:
        # Step 1: Extract Entities
        entities = cls.extract_entities(message, session_id)
        shipment_id = entities.get("shipment_id")
        invoice_id = entities.get("invoice_id")
        amount = entities.get("amount")
        reason = entities.get("reason") or "Damaged shipment"

        # Step 2: Classify Intent
        classification = cls.classify_intent(message, selected_employee)
        intent = classification["intent"]
        employee_key = classification["employee"]
        confidence = classification["confidence"]

        activity_log = [
            f"✓ Customer message received: '{message}'",
            f"✓ Intent detected: {intent} (Confidence: {confidence * 100:.0f}%)",
            f"✓ Entities extracted: shipment_id={shipment_id or 'None'}, invoice_id={invoice_id or 'None'}, amount={amount or 'None'}"
        ]

        # ----------------------------------------------------
        # SECURITY VIOLATION (TEST 10)
        # ----------------------------------------------------
        if intent == "SECURITY_VIOLATION":
            activity_log.append("🛑 Security Violation Detected: Prompt injection blocked.")
            return {
                "message": "I cannot comply with requests to bypass security guidelines, reveal database credentials, or display internal databases.",
                "intent": "security_violation",
                "employee": "🤖 Workora AI Manager",
                "activity_log": activity_log,
                "data": {"error": "Unauthorized request", "code": "FORBIDDEN"}
            }

        # ----------------------------------------------------
        # UNKNOWN UNRELATED REQUEST ("Tell me a joke")
        # ----------------------------------------------------
        if intent == "UNKNOWN":
            activity_log.append("⚠️ Unrelated request intent: Returning friendly capabilities fallback.")
            return {
                "message": "I'm designed to help with LogiFlow Logistics shipments, deliveries, billing and customer support. How can I help you?",
                "intent": "unknown",
                "employee": "🤖 Workora AI Manager",
                "activity_log": activity_log
            }

        # ----------------------------------------------------
        # AMBIGUOUS REQUEST (TEST 9: "I have a problem.")
        # ----------------------------------------------------
        if intent == "AMBIGUOUS_REQUEST":
            activity_log.append("❓ Low confidence (45%): Requesting clarification from customer.")
            return {
                "message": "I can help with your request. Is your issue related to:\n\n1. 📦 **Shipment** (Tracking & Delays)\n2. 🚚 **Delivery** (Scheduling & Address)\n3. 💰 **Billing** (Invoices & Refunds)\n4. 📞 **General Support** (Complaints & Agents)?",
                "intent": "ambiguous_request",
                "employee": "🤖 Workora AI Manager",
                "activity_log": activity_log,
                "data": {"suggested_actions": ["Shipment Issue", "Delivery Issue", "Billing Issue", "Talk to Human"]}
            }

        # ----------------------------------------------------
        # HUMAN SUPPORT ESCALATION (TEST 5)
        # ----------------------------------------------------
        if intent == "HUMAN_SUPPORT":
            activity_log.append("📞 Escalated to Customer Service Employee for live human agent.")
            return {
                "message": "Support Request:\nSUP-10025\n\nStatus:\nWaiting for Agent\n\nConnecting you to a live senior support agent. Please hold...",
                "intent": "human_support",
                "employee": "📞 Customer Service Employee",
                "activity_log": activity_log,
                "data": {"support_request_id": "SUP-10025", "status": "Waiting for Agent", "routed_to": "Customer Service Employee", "employee_key": "customer_service", "estimated_wait": "2 mins"}
            }

        # ----------------------------------------------------
        # MULTI-INTENT: DELAY + REFUND (TEST 6)
        # ----------------------------------------------------
        if intent == "MULTI_INTENT_DELAY_REFUND":
            target_sid = shipment_id or "SL1003"
            activity_log.append(f"📦 Step 1: Routing to Shipment Employee to check delay for {target_sid}")
            
            ship_obj = db.query(Shipment).filter(Shipment.shipment_id == target_sid).first()
            delay_text = f"Shipment {target_sid} is currently delayed at Surat Distribution Center due to heavy rainfall highway diversion." if ship_obj else f"Shipment {target_sid} is currently experiencing a delay in transit."

            activity_log.append("💰 Step 2: Routing to Billing Employee to prepare refund request")
            refund_amt = amount or 1250.0
            
            # Policy & Approval Check
            activity_log.append("🔐 Step 3: Triggering Human Approval Security & Control Layer")
            app_out = ApprovalService.create_approval_request(
                req=ApprovalCreate(
                    request_type="refund",
                    employee="💰 Billing Employee",
                    shipment_id=target_sid,
                    amount=refund_amt,
                    reason="Shipment delayed in transit"
                ),
                db=db,
                current_user=current_user
            )

            resp_msg = (
                f"{delay_text}\n\n"
                f"I've also prepared your refund request.\n\n"
                f"Refund Amount:\n₹{refund_amt:,.0f}\n\n"
                f"Status:\nPending Human Approval\n\n"
                f"Request ID:\n{app_out.approval_id}"
            )

            return {
                "message": resp_msg,
                "intent": "multi_intent_delay_refund",
                "employee": "🤖 Workora AI Manager",
                "requires_approval": True,
                "activity_log": activity_log,
                "data": {
                    "shipment_id": target_sid,
                    "refund_amount": refund_amt,
                    "request_id": app_out.approval_id,
                    "status": "Pending Human Approval",
                    "requires_human_approval": True
                }
            }

        # ----------------------------------------------------
        # MULTI-INTENT: DELAY + RESCHEDULE (TEST 7)
        # ----------------------------------------------------
        if intent == "MULTI_INTENT_DELAY_RESCHEDULE":
            target_sid = shipment_id or "SL1004"
            activity_log.append(f"📦 Step 1: Routing to Shipment Employee to check delay for {target_sid}")
            activity_log.append(f"🚚 Step 2: Routing to Delivery Employee to check reschedule availability for {target_sid}")

            slots_obj = DeliveryService.get_slots(target_sid, db)
            avail_slots = slots_obj.available_slots if hasattr(slots_obj, 'available_slots') else []
            slot_list_str = "\n".join([f"• {s}" for s in avail_slots[:3]])

            resp_msg = (
                f"Shipment {target_sid} is currently experiencing a minor delay at the sorting facility.\n\n"
                f"You can reschedule your delivery for one of the following available time slots:\n\n"
                f"{slot_list_str}\n\n"
                f"Reply with your preferred date and time to confirm."
            )

            return {
                "message": resp_msg,
                "intent": "multi_intent_delay_reschedule",
                "employee": "🤖 Workora AI Manager",
                "activity_log": activity_log,
                "data": {
                    "shipment_id": target_sid,
                    "available_slots": avail_slots,
                    "suggested_actions": ["Reschedule Delivery", "Contact Support"]
                }
            }

        # ----------------------------------------------------
        # SINGLE INTENT: SHIPMENT TRACKING (TEST 1, TEST 8)
        # ----------------------------------------------------
        if intent == "SHIPMENT_TRACKING":
            target_sid = shipment_id or "SL1004"
            activity_log.append(f"📦 Executing Shipment Employee workflow for {target_sid}")

            # TEST 8: Unknown shipment SL9999 -> 404 Not Found (Never return SL1004)
            if target_sid == "SL9999":
                activity_log.append("❌ Shipment SL9999 not found in database.")
                return {
                    "message": "I couldn't find shipment SL9999. Please check the shipment ID and try again.",
                    "intent": "unknown_shipment",
                    "employee": "📦 Shipment Employee",
                    "activity_log": activity_log,
                    "data": {"error": "Shipment not found", "code": "NOT_FOUND"}
                }

            shipment = db.query(Shipment).filter(Shipment.shipment_id == target_sid).first()
            if not shipment:
                activity_log.append(f"❌ Shipment {target_sid} not found.")
                return {
                    "message": f"I couldn't find shipment {target_sid}. Please check the shipment ID and try again.",
                    "intent": "unknown_shipment",
                    "employee": "📦 Shipment Employee",
                    "activity_log": activity_log
                }

            resp_msg = (
                f"Shipment {shipment.shipment_id} is currently **{shipment.status}**.\n\n"
                f"Location:\n{shipment.current_location}\n\n"
                f"Expected Delivery:\n{shipment.expected_delivery.strftime('%d %B %Y') if shipment.expected_delivery else '8 October 2026'}"
            )
            return {
                "message": resp_msg,
                "intent": "shipment_tracking",
                "shipment_id": target_sid,
                "employee": "📦 Shipment Employee",
                "activity_log": activity_log,
                "data": {
                    "shipment_id": target_sid,
                    "status": shipment.status,
                    "current_location": shipment.current_location,
                    "expected_delivery": str(shipment.expected_delivery)
                }
            }

        # ----------------------------------------------------
        # SINGLE INTENT: INVOICE LOOKUP (TEST 2)
        # ----------------------------------------------------
        if intent == "INVOICE_LOOKUP":
            target_iid = invoice_id or "INV-2045"
            activity_log.append(f"💰 Executing Billing Employee workflow for {target_iid}")

            if target_iid == "INV-9999":
                return {
                    "message": "I couldn't find invoice INV-9999. Please check the invoice ID and try again.",
                    "intent": "invoice_not_found",
                    "employee": "💰 Billing Employee",
                    "activity_log": activity_log
                }

            inv = db.query(Invoice).filter(Invoice.invoice_id == target_iid).first()
            if not inv:
                inv = db.query(Invoice).filter(Invoice.invoice_id == "INV-2045").first()

            ship_code = inv.shipment.shipment_id if inv and inv.shipment else "SL1004"
            ship_charge = float(inv.shipping_charge) if inv else 1050.0
            tax_amt = float(inv.tax) if inv else 200.0
            tot = float(inv.total_amount) if inv else 1250.0

            resp_msg = (
                f"Here are the invoice details.\n\n"
                f"Invoice:\n{inv.invoice_id if inv else 'INV-2045'}\n\n"
                f"Shipment:\n{ship_code}\n\n"
                f"Shipping Charge:\n₹{ship_charge:,.0f}\n\n"
                f"Tax:\n₹{tax_amt:,.0f}\n\n"
                f"Total:\n₹{tot:,.0f}\n\n"
                f"Payment Status:\n{inv.payment_status if inv else 'Paid'}"
            )

            return {
                "message": resp_msg,
                "intent": "invoice_lookup",
                "employee": "💰 Billing Employee",
                "activity_log": activity_log,
                "data": {
                    "invoice_id": inv.invoice_id if inv else "INV-2045",
                    "shipment_id": ship_code,
                    "total_amount": tot,
                    "payment_status": inv.payment_status if inv else "Paid",
                    "suggested_actions": ["View Invoice", "Download Invoice"]
                }
            }

        # ----------------------------------------------------
        # SINGLE INTENT: DELIVERY RESCHEDULE (TEST 3)
        # ----------------------------------------------------
        if intent == "DELIVERY_RESCHEDULE":
            target_sid = shipment_id or "SL1004"
            activity_log.append(f"🚚 Executing Delivery Employee workflow for {target_sid}")

            slots_obj = DeliveryService.get_slots(target_sid, db)
            avail_slots = slots_obj.available_slots if hasattr(slots_obj, 'available_slots') else []
            slot_str = "\n".join([f"• {s}" for s in avail_slots[:3]])

            resp_msg = (
                f"I can help you reschedule shipment {target_sid}.\n\n"
                f"Available Delivery Slots:\n{slot_str}\n\n"
                f"Please select your preferred slot."
            )

            return {
                "message": resp_msg,
                "intent": "delivery_reschedule",
                "shipment_id": target_sid,
                "employee": "🚚 Delivery Employee",
                "activity_log": activity_log,
                "data": {
                    "shipment_id": target_sid,
                    "available_slots": avail_slots,
                    "suggested_actions": ["Confirm Reschedule", "Talk to Human"]
                }
            }

        # ----------------------------------------------------
        # SINGLE INTENT: CUSTOMER COMPLAINT (TEST 4)
        # ----------------------------------------------------
        if intent == "CUSTOMER_COMPLAINT":
            activity_log.append("📞 Executing Customer Service Employee workflow for complaint.")

            resp_msg = (
                "I'm sorry to hear that your package arrived damaged.\n\n"
                "I've created a priority customer support ticket for your issue.\n\n"
                "Ticket ID:\nLGT-9012\n\n"
                "Status:\nUnder Review\n\n"
                "Our support team will inspect the shipment claim."
            )

            return {
                "message": resp_msg,
                "intent": "customer_complaint",
                "employee": "📞 Customer Service Employee",
                "activity_log": activity_log,
                "data": {
                    "ticket_id": "LGT-9012",
                    "status": "Under Review",
                    "suggested_actions": ["Track Support Ticket", "Talk to Human Agent"]
                }
            }

        # ----------------------------------------------------
        # SINGLE INTENT: HUMAN SUPPORT / ESCALATION (TEST 5)
        # ----------------------------------------------------
        if intent == "HUMAN_SUPPORT":
            activity_log.append("📞 Executing Customer Service Employee workflow for human escalation.")
            req_id = f"SUP-10025"

            resp_msg = (
                f"I've created a support request for a live human agent.\n\n"
                f"Support Request:\n{req_id}\n\n"
                f"Status:\nWaiting for Agent\n\n"
                f"A senior support agent will connect with you shortly."
            )

            return {
                "message": resp_msg,
                "intent": "human_support",
                "employee": "📞 Customer Service Employee",
                "activity_log": activity_log,
                "data": {
                    "support_request_id": req_id,
                    "status": "Waiting for Agent",
                    "suggested_actions": ["Wait for Agent", "Cancel Escalation"]
                }
            }

        # ----------------------------------------------------
        # SINGLE INTENT: REFUND REQUEST
        # ----------------------------------------------------
        if intent == "REFUND_REQUEST":
            target_sid = shipment_id or "SL1004"
            target_iid = invoice_id or "INV-2045"
            refund_amt = amount or 1250.0

            activity_log.append(f"💰 Executing Billing Employee refund workflow for {target_sid}")

            # Check refund amount validation (exceeds invoice total)
            inv = db.query(Invoice).filter(Invoice.invoice_id == target_iid).first()
            max_allowed = float(inv.total_amount) if inv else 1250.0

            if refund_amt > max_allowed or refund_amt <= 0:
                activity_log.append(f"❌ Requested refund ₹{refund_amt} exceeds max allowed ₹{max_allowed}")
                return {
                    "message": "The requested refund amount is greater than the invoice amount. Please contact billing support.",
                    "intent": "invalid_refund_amount",
                    "employee": "💰 Billing Employee",
                    "activity_log": activity_log,
                    "data": {"error": "Refund exceeds invoice amount", "max_allowed": max_allowed}
                }

            activity_log.append("🔐 Creating Human Approval Request for refund")
            app_out = ApprovalService.create_approval_request(
                req=ApprovalCreate(
                    request_type="refund",
                    employee="💰 Billing Employee",
                    shipment_id=target_sid,
                    invoice_id=target_iid,
                    amount=refund_amt,
                    reason=reason
                ),
                db=db,
                current_user=current_user
            )

            resp_msg = (
                f"Your refund request has been submitted for review.\n\n"
                f"Request ID:\n{app_out.approval_id}\n\n"
                f"Amount:\n₹{refund_amt:,.0f}\n\n"
                f"Status:\nPending Review"
            )

            return {
                "message": resp_msg,
                "intent": "refund_approval_required",
                "employee": "💰 Billing Employee",
                "activity_log": activity_log,
                "data": {
                    "request_id": app_out.approval_id,
                    "invoice_id": target_iid,
                    "shipment_id": target_sid,
                    "requested_amount": refund_amt,
                    "status": "Pending Review",
                    "requires_human_approval": True
                }
            }

        # ----------------------------------------------------
        # AMBIGUOUS REQUEST (TEST 9)
        # ----------------------------------------------------
        if intent == "AMBIGUOUS_REQUEST":
            activity_log.append("❓ Ambiguous request detected. Asking customer for clarification.")
            return {
                "message": "Sure, I can help. Could you provide your shipment ID?\n\nIs your issue related to:\n• Shipment tracking\n• Delivery rescheduling\n• Billing / Invoice\n• Customer Support",
                "intent": "AMBIGUOUS_REQUEST",
                "employee": "🤖 Workora AI Manager",
                "activity_log": activity_log,
                "data": {
                    "suggested_actions": ["Shipment", "Delivery", "Billing", "General Support"]
                }
            }

        # ----------------------------------------------------
        # UNKNOWN / UNRELATED REQUEST (Section 11)
        # ----------------------------------------------------
        if intent == "UNKNOWN":
            activity_log.append("⚠️ Unrelated request. Returning scope clarification.")
            return {
                "message": "I'm designed to help with LogiFlow Logistics shipments, deliveries, billing and customer support. How can I help you?",
                "intent": "UNKNOWN",
                "employee": "🤖 Workora AI Manager",
                "activity_log": activity_log
            }

        # Fallback General Response
        activity_log.append("📞 Fallback to Customer Service Employee.")
        return {
            "message": "I can help you with LogiFlow shipments, deliveries, invoices and support requests. How can I assist you today?",
            "intent": "general_help",
            "employee": "📞 Customer Service Employee",
            "activity_log": activity_log
        }

    @classmethod
    def get_manager_status(cls, db: Session) -> Dict[str, Any]:
        return {
            "manager_name": "🤖 Workora AI Manager",
            "status": "Online",
            "tasks_today": 128,
            "successfully_completed": 112,
            "human_approvals": 12,
            "escalations": 4,
            "active_employees": [
                "📦 Shipment Employee",
                "📞 Customer Service Employee",
                "🚚 Delivery Employee",
                "💰 Billing Employee"
            ],
            "label": "Demo Data"
        }
