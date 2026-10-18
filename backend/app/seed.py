"""
LogiFlow Logistics - Database Demo Seed Script
Populates fictional demo customers, shipments, delivery events, delivery assignments,
tickets, invoices, refund requests, conversations, chat messages, and knowledge documents.
"""

import datetime
from .database import SessionLocal, engine, Base
from .models.customer import Customer
from .models.shipment import Shipment
from .models.delivery_event import DeliveryEvent
from .models.delivery_assignment import DeliveryAssignment
from .models.ticket import Ticket
from .models.invoice import Invoice
from .models.refund_request import RefundRequest
from .models.conversation import Conversation
from .models.chat_message import ChatMessage
from .models.knowledge_document import KnowledgeDocument
from .models.audit_log import AuditLog
from .models.delivery_record import DeliveryRecord
from .models.approval_request import ApprovalRequest
from .auth import get_password_hash

def seed_database():
    print("[*] Recreating LogiFlow relational database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:

        print("[*] Seeding demo customers...")
        default_pwd = get_password_hash("password123")

        c1 = Customer(customer_id="CUST001", name="Rahul Patel", email="rahul@example.com", phone="+919900000001", password_hash=default_pwd, role="customer", address="402 Orchid Heights, SG Highway", city="Ahmedabad", state="Gujarat")
        c2 = Customer(customer_id="CUST002", name="Priya Shah", email="priya@example.com", phone="+919900000002", password_hash=default_pwd, role="customer", address="12 Silver Palm Residency, Ring Road", city="Surat", state="Gujarat")
        c3 = Customer(customer_id="CUST003", name="Amit Mehta", email="amit@example.com", phone="+919900000003", password_hash=default_pwd, role="customer", address="705 Navrang Square, Kalawad Road", city="Rajkot", state="Gujarat")
        c4 = Customer(customer_id="CUST004", name="Neha Shah", email="neha@example.com", phone="+919900000004", password_hash=default_pwd, role="customer", address="B-402, Riverfront Heights, Ashram Road", city="Ahmedabad", state="Gujarat")
        c5 = Customer(customer_id="CUST005", name="Jay Patel", email="jay@example.com", phone="+919900000005", password_hash=default_pwd, role="customer", address="55 Station Road", city="Jamnagar", state="Gujarat")
        c_admin = Customer(customer_id="ADMIN001", name="LogiFlow Admin", email="admin@logiflow.com", phone="+919900000000", password_hash=default_pwd, role="admin", address="LogiFlow HQ", city="Ahmedabad", state="Gujarat")

        db.add_all([c1, c2, c3, c4, c5, c_admin])
        db.commit()
        for c in [c1, c2, c3, c4, c5, c_admin]:
            db.refresh(c)

        print("[*] Seeding demo shipments (SL1001 - SL1005 and LG series)...")
        sl1 = Shipment(
            shipment_id="SL1001", customer_id=c1.id, tracking_number="TRK-SL1001-99", status="Delivered",
            current_location="Ahmedabad", origin="Chennai Port Hub", destination="Ahmedabad",
            expected_delivery=datetime.date(2026, 10, 5), actual_delivery=datetime.date(2026, 10, 5),
            package_type="Electronics Box", weight_kg=2.50, shipping_charge=450.00,
            carrier="LogiFlow Express", last_update="Package delivered to customer", delay_reason=None
        )
        sl2 = Shipment(
            shipment_id="SL1002", customer_id=c2.id, tracking_number="TRK-SL1002-99", status="In Transit",
            current_location="Rajkot", origin="Mumbai DC", destination="Rajkot",
            expected_delivery=datetime.date(2026, 10, 7), package_type="Standard Parcel", weight_kg=1.20, shipping_charge=280.00,
            carrier="LogiFlow Air", last_update="Departed Rajkot Facility", delay_reason=None
        )
        sl3 = Shipment(
            shipment_id="SL1003", customer_id=c3.id, tracking_number="TRK-SL1003-99", status="Delayed",
            current_location="Surat Distribution Center", origin="Delhi Gateway", destination="Surat",
            expected_delivery=datetime.date(2026, 10, 9), package_type="Industrial Spares", weight_kg=12.50, shipping_charge=1800.00,
            carrier="LogiFlow Surface", last_update="Delayed at Surat DC", delay_reason="Transportation delay."
        )
        sl4 = Shipment(
            shipment_id="SL1004", customer_id=c1.id, tracking_number="TRK-SL1004-99", status="In Transit",
            current_location="Ahmedabad Sorting Facility", origin="Bhiwandi Hub, Mumbai, MH", destination="B-402, Riverfront Heights, Ashram Road, Ahmedabad, GJ",
            expected_delivery=datetime.date(2026, 10, 8), package_type="Electronic Components (Fragile)", weight_kg=2.80, shipping_charge=1250.00,
            carrier="LogiFlow Express Air", last_update="Arrived at sorting facility", delay_reason=None
        )
        sl5 = Shipment(
            shipment_id="SL1005", customer_id=c5.id, tracking_number="TRK-SL1005-99", status="Out for Delivery",
            current_location="Jamnagar", origin="Rajkot Hub", destination="Jamnagar",
            expected_delivery=datetime.date(2026, 10, 7), package_type="Apparel Carton", weight_kg=6.00, shipping_charge=650.00,
            carrier="LogiFlow Express", last_update="Out for delivery with courier", delay_reason=None
        )

        all_shipments = [sl1, sl2, sl3, sl4, sl5]
        db.add_all(all_shipments)
        db.commit()
        for s in all_shipments:
            db.refresh(s)

        print("[*] Seeding delivery events timeline...")
        events = [
            # Events for SL1004
            DeliveryEvent(shipment_id=sl4.id, status="Order Confirmed", location="Bhiwandi Gateway Hub", description="Order received and verified.", event_time=datetime.datetime(2026, 10, 5, 10, 30)),
            DeliveryEvent(shipment_id=sl4.id, status="Picked Up", location="Bhiwandi Gateway Hub", description="Package picked up by express cargo team.", event_time=datetime.datetime(2026, 10, 5, 15, 15)),
            DeliveryEvent(shipment_id=sl4.id, status="In Transit", location="Ahmedabad Sorting Facility", description="Arrived at sorting facility and scheduled for local delivery dispatch.", event_time=datetime.datetime(2026, 10, 7, 14, 45)),
            
            # Events for SL1001
            DeliveryEvent(shipment_id=sl1.id, status="Order Confirmed", location="Chennai Port Hub", description="Consignment registered.", event_time=datetime.datetime(2026, 10, 1, 10, 0)),
            DeliveryEvent(shipment_id=sl1.id, status="Picked Up", location="Chennai Hub", description="Picked up.", event_time=datetime.datetime(2026, 10, 1, 15, 0)),
            DeliveryEvent(shipment_id=sl1.id, status="In Transit", location="Vijayawada Crossdock", description="In transit via national highway.", event_time=datetime.datetime(2026, 10, 2, 8, 0)),
            DeliveryEvent(shipment_id=sl1.id, status="Out for Delivery", location="Ahmedabad", description="Out for final mile delivery.", event_time=datetime.datetime(2026, 10, 5, 11, 0)),
            DeliveryEvent(shipment_id=sl1.id, status="Delivered", location="Ahmedabad", description="Package delivered to customer.", event_time=datetime.datetime(2026, 10, 5, 15, 45)),

            # Events for SL1003
            DeliveryEvent(shipment_id=sl3.id, status="Order Confirmed", location="Delhi Gateway", description="Booking confirmed.", event_time=datetime.datetime(2026, 10, 4, 9, 0)),
            DeliveryEvent(shipment_id=sl3.id, status="Picked Up", location="Delhi Gate", description="Picked up.", event_time=datetime.datetime(2026, 10, 4, 14, 0)),
            DeliveryEvent(shipment_id=sl3.id, status="Delayed", location="Surat Distribution Center", description="Transportation delay.", event_time=datetime.datetime(2026, 10, 7, 11, 30)),

            # Events for SL1005
            DeliveryEvent(shipment_id=sl5.id, status="Order Confirmed", location="Rajkot Hub", description="Package accepted at warehouse.", event_time=datetime.datetime(2026, 10, 6, 12, 0)),
            DeliveryEvent(shipment_id=sl5.id, status="Out for Delivery", location="Jamnagar", description="Driver out on delivery route.", event_time=datetime.datetime(2026, 10, 7, 8, 30))
        ]
        db.add_all(events)

        print("[*] Seeding delivery assignments...")
        assignments = [
            DeliveryAssignment(shipment_id=sl4.id, driver_name="Ramesh Solanki", driver_phone="+919800000010", vehicle_number="GJ-01-AB-1234", vehicle_type="Express Van", assignment_status="In Transit", scheduled_date=datetime.date(2026, 10, 8)),
            DeliveryAssignment(shipment_id=sl5.id, driver_name="Vijay Rathod", driver_phone="+919800000011", vehicle_number="GJ-10-CD-5678", vehicle_type="Delivery Bike", assignment_status="Out for Delivery", scheduled_date=datetime.date(2026, 10, 7))
        ]
        db.add_all(assignments)

        print("[*] Seeding demo delivery records (SL1001 - SL1005)...")
        dr1 = DeliveryRecord(
            delivery_id="DLV-1001", shipment_id="SL1001", customer_id=c1.id,
            delivery_status="Delivered", expected_date=datetime.date(2026, 10, 5),
            delivery_window="10:00 AM – 1:00 PM", delivery_address="402 Orchid Heights, SG Highway, Ahmedabad, GJ",
            driver_id="DRV-801", driver_name="Ramesh Solanki", attempt_count=1, last_attempt="5 October 2026 · 3:45 PM",
            reschedule_allowed=False, available_slots=[]
        )
        dr2 = DeliveryRecord(
            delivery_id="DLV-1002", shipment_id="SL1002", customer_id=c2.id,
            delivery_status="In Transit", expected_date=datetime.date(2026, 10, 7),
            delivery_window="2:00 PM – 5:00 PM", delivery_address="12 Silver Palm Residency, Ring Road, Surat, GJ",
            driver_id="DRV-802", driver_name="Sanjay Patel", attempt_count=0,
            reschedule_allowed=True, available_slots=["8 October — 10 AM–1 PM", "8 October — 2 PM–5 PM", "9 October — 10 AM–1 PM"]
        )
        dr3 = DeliveryRecord(
            delivery_id="DLV-1003", shipment_id="SL1003", customer_id=c3.id,
            delivery_status="Failed Delivery", expected_date=datetime.date(2026, 10, 7),
            delivery_window="2:00 PM – 5:00 PM", delivery_address="705 Navrang Square, Kalawad Road, Rajkot, GJ",
            driver_id="DRV-803", driver_name="Vikram Singh", attempt_count=1, last_attempt="7 October 2026 · 3:20 PM",
            exception_type="Delivery Failure", exception_reason="Customer unavailable",
            reschedule_allowed=True, available_slots=["8 October — 10 AM–1 PM", "8 October — 2 PM–5 PM", "9 October — 10 AM–1 PM"]
        )
        dr4 = DeliveryRecord(
            delivery_id="DLV-1004", shipment_id="SL1004", customer_id=c1.id,
            delivery_status="In Transit", expected_date=datetime.date(2026, 10, 8),
            delivery_window="2:00 PM – 5:00 PM", delivery_address="B-402, Riverfront Heights, Ashram Road, Ahmedabad, GJ",
            driver_id="DRV-804", driver_name="Ramesh Solanki", attempt_count=0,
            reschedule_allowed=True, available_slots=["9 October — 10 AM–1 PM", "9 October — 2 PM–5 PM", "10 October — 10 AM–1 PM"]
        )
        dr5 = DeliveryRecord(
            delivery_id="DLV-1005", shipment_id="SL1005", customer_id=c5.id,
            delivery_status="Out for Delivery", expected_date=datetime.date(2026, 10, 7),
            delivery_window="9:00 AM – 1:00 PM", delivery_address="55 Station Road, Jamnagar, GJ",
            driver_id="DRV-805", driver_name="Vijay Rathod", attempt_count=0,
            reschedule_allowed=False, available_slots=[]
        )
        db.add_all([dr1, dr2, dr3, dr4, dr5])

        print("[*] Seeding demo tickets...")
        t1 = Ticket(
            ticket_id="LGT-1021",
            customer_id=c2.id,
            shipment_id=sl3.id,
            issue_type="Delivery Delay",
            issue="Shipment SL1003 is showing delay at Surat facility. Need urgent status for production line.",
            priority="High",
            status="In Progress",
            assigned_to="Priya Nair (Operations)"
        )
        t2 = Ticket(
            ticket_id="LGT-1024",
            customer_id=c3.id,
            shipment_id=sl5.id,
            issue_type="Damaged Package",
            issue="Outer box carton appears crushed upon loading inspection.",
            priority="Medium",
            status="Under Review",
            assigned_to="Karan Verma (Quality)"
        )
        db.add_all([t1, t2])

        print("[*] Seeding demo invoices (INV-2041 to INV-2046)...")
        inv_41 = Invoice(
            invoice_id="INV-2041", customer_id=c1.id, shipment_id=sl1.id,
            shipping_charge=750.00, tax=150.00, total_amount=900.00,
            payment_status="Paid", invoice_date=datetime.date(2026, 10, 2), payment_date=datetime.date(2026, 10, 3)
        )
        inv_42 = Invoice(
            invoice_id="INV-2042", customer_id=c1.id, shipment_id=sl2.id,
            shipping_charge=900.00, tax=180.00, total_amount=1080.00,
            payment_status="Paid", invoice_date=datetime.date(2026, 10, 3), payment_date=datetime.date(2026, 10, 4)
        )
        inv_43 = Invoice(
            invoice_id="INV-2043", customer_id=c1.id, shipment_id=sl3.id,
            shipping_charge=800.00, tax=160.00, total_amount=960.00,
            payment_status="Pending", invoice_date=datetime.date(2026, 10, 5), due_date=datetime.date(2026, 10, 10)
        )
        inv_44 = Invoice(
            invoice_id="INV-2044", customer_id=c1.id, shipment_id=sl5.id,
            shipping_charge=1000.00, tax=200.00, total_amount=1200.00,
            payment_status="Paid", invoice_date=datetime.date(2026, 10, 5), payment_date=datetime.date(2026, 10, 6)
        )
        inv_45 = Invoice(
            invoice_id="INV-2045", customer_id=c1.id, shipment_id=sl4.id,
            shipping_charge=1050.00, tax=200.00, total_amount=1250.00,
            payment_status="Paid", invoice_date=datetime.date(2026, 10, 6), payment_date=datetime.date(2026, 10, 7)
        )
        inv_46 = Invoice(
            invoice_id="INV-2046", customer_id=c2.id, shipment_id=sl2.id,
            shipping_charge=1500.00, tax=300.00, total_amount=1800.00,
            payment_status="Pending", invoice_date=datetime.date(2026, 10, 6), due_date=datetime.date(2026, 10, 20)
        )
        all_invoices = [inv_41, inv_42, inv_43, inv_44, inv_45, inv_46]
        db.add_all(all_invoices)
        db.commit()
        for inv in all_invoices:
            db.refresh(inv)

        print("[*] Seeding demo refund requests...")
        ref1 = RefundRequest(
            refund_id="REF-001",
            customer_id=c3.id,
            shipment_id=sl5.id,
            invoice_id=None,
            amount=2000.00,
            reason="Damaged goods claim filed during shipment handling.",
            status="Pending Approval",
            approved_by=None,
            approved_at=None
        )
        db.add(ref1)

        print("[*] Seeding sample conversations and chatbot messages...")
        conv1 = Conversation(
            conversation_id="CONV-1001",
            customer_id=c1.id,
            title="Shipment Tracking Inquiry SL1004",
            channel="web",
            status="Active"
        )
        db.add(conv1)
        db.commit()
        db.refresh(conv1)

        m1 = ChatMessage(
            conversation_id=conv1.id,
            sender_type="customer",
            message="Where is my shipment SL1004?",
            intent="shipment_tracking"
        )
        m2 = ChatMessage(
            conversation_id=conv1.id,
            sender_type="ai",
            message="Shipment SL1004 is currently in transit at Ahmedabad Distribution Center.",
            intent="shipment_tracking"
        )
        db.add_all([m1, m2])

        print("[*] Seeding knowledge documents...")
        docs = [
            KnowledgeDocument(
                document_id="DOC-POL-01",
                title="LogiFlow Standard Refund & Damage Policy",
                category="Policies",
                content="Refund requests for damaged or delayed shipments require photo evidence and supervisory approval within 7 business days."
            ),
            KnowledgeDocument(
                document_id="DOC-SLA-02",
                title="LogiFlow Express Delivery SLAs",
                category="Operations",
                content="Intra-state shipments in Gujarat are delivered within 24-48 hours. Inter-state cargo moves via national express lanes in 3-5 days."
            )
        ]
        db.add_all(docs)

        print("[*] Seeding initial human approval requests...")
        apr1 = ApprovalRequest(
            approval_id="APR-10024",
            request_type="refund",
            employee="💰 Billing Employee",
            customer_id=c1.id,
            shipment_id=sl4.id,
            invoice_id=inv_45.id,
            amount=2000.00,
            reason="Damaged shipment",
            requested_action="Refund ₹2,000",
            status="Pending Approval",
            priority="Medium"
        )
        apr2 = ApprovalRequest(
            approval_id="APR-10025",
            request_type="address_change",
            employee="🚚 Delivery Employee",
            customer_id=c1.id,
            shipment_id=sl4.id,
            amount=0.00,
            reason="Customer requested address update prior to delivery attempt",
            requested_action="Change delivery address to B-402, Riverfront Heights, Ashram Road",
            status="Pending Approval",
            priority="Low"
        )
        apr3 = ApprovalRequest(
            approval_id="APR-10026",
            request_type="cancellation",
            employee="📦 Shipment Employee",
            customer_id=c3.id,
            shipment_id=sl3.id,
            amount=0.00,
            reason="Shipper cancelled order due to inventory shortage",
            requested_action="Cancel Shipment SL1003",
            status="Approved",
            priority="High",
            reviewed_by="LogiFlow Supervisor",
            reviewed_at=datetime.datetime.now(),
            review_comment="Cancellation verified with merchant."
        )
        apr4 = ApprovalRequest(
            approval_id="APR-10027",
            request_type="refund",
            employee="💰 Billing Employee",
            customer_id=c1.id,
            shipment_id=sl4.id,
            invoice_id=inv_45.id,
            amount=15000.00,
            reason="Customer requested full claim compensation beyond invoice amount",
            requested_action="Refund ₹15,000",
            status="Rejected",
            priority="Critical",
            reviewed_by="LogiFlow Admin",
            reviewed_at=datetime.datetime.now(),
            review_comment="Refund exceeds maximum policy limit of ₹1,250."
        )
        db.add_all([apr1, apr2, apr3, apr4])

        print("[*] Seeding initial audit logs...")
        audit = AuditLog(
            customer_id=c1.id,
            action="Shipment Tracking Query",
            entity_type="shipment",
            entity_id="SL1004",
            result="Success",
            details={"ip": "127.0.0.1", "channel": "web_chat"}
        )
        db.add(audit)

        db.commit()
        print("[OK] Successfully seeded all LogiFlow Logistics demo data.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
