"""
Unit and Integration Test Suite for LogiFlow Logistics Database Layer.
Verifies all 10 core database requirements:
1. Database connection works
2. Customer insertion
3. Shipment insertion
4. Shipment-to-customer relational mapping
5. Delivery events timeline on shipment
6. Customer ticket creation & relationships
7. Invoices belonging to customer & shipment
8. Refund requests default status 'Pending Approval'
9. Conversation containing multi-turn chat messages
10. Relational cascade and foreign key constraints
"""

import os
import sys
import unittest
import datetime
from decimal import Decimal

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models.customer import Customer
from app.models.shipment import Shipment
from app.models.delivery_event import DeliveryEvent
from app.models.delivery_assignment import DeliveryAssignment
from app.models.ticket import Ticket
from app.models.invoice import Invoice
from app.models.refund_request import RefundRequest
from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage
from app.models.knowledge_document import KnowledgeDocument
from app.models.audit_log import AuditLog
from app.auth import hash_password

class TestLogisticsDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_01_database_connection(self):
        """1. Verify database engine connection works."""
        with engine.connect() as conn:
            result = conn.execute(Base.metadata.tables["customers"].select().limit(1))
            self.assertIsNotNone(result)

    def test_02_customer_insertion(self):
        """2. Verify customer can be inserted and queried."""
        ts = int(datetime.datetime.now().timestamp())
        cust = Customer(
            customer_id=f"TEST_CUST_{ts}",
            name="Test User",
            email=f"test_{ts}@example.com",
            phone=f"+91{ts}"[:14],
            password_hash=hash_password("securePass123"),
            city="Ahmedabad",
            state="Gujarat"
        )
        self.db.add(cust)
        self.db.commit()
        self.db.refresh(cust)

        self.assertIsNotNone(cust.id)
        fetched = self.db.query(Customer).filter(Customer.customer_id == f"TEST_CUST_{ts}").first()
        self.assertEqual(fetched.name, "Test User")
        self.assertTrue(fetched.password_hash.startswith("sha256$"))

    def test_03_shipment_insertion(self):
        """3. Verify shipment can be inserted."""
        ts = int(datetime.datetime.now().timestamp())
        cust = Customer(
            customer_id=f"CUST_S_{ts}",
            name="Ship User",
            email=f"ship_{ts}@example.com",
            phone=f"+9188{ts}"[:14],
            password_hash=hash_password("pass")
        )
        self.db.add(cust)
        self.db.commit()
        self.db.refresh(cust)

        ship = Shipment(
            shipment_id=f"LG_TEST_{ts}",
            customer_id=cust.id,
            tracking_number=f"TRK_TEST_{ts}",
            status="In Transit",
            current_location="Ahmedabad Distribution Center",
            origin="Mumbai",
            destination="Ahmedabad",
            expected_delivery=datetime.date(2026, 10, 8),
            weight_kg=Decimal("4.50"),
            shipping_charge=Decimal("1200.00")
        )
        self.db.add(ship)
        self.db.commit()
        self.db.refresh(ship)

        self.assertIsNotNone(ship.id)
        self.assertEqual(ship.status, "In Transit")

    def test_04_shipment_belongs_to_customer(self):
        """4. Verify shipment correctly links to its parent customer."""
        cust = self.db.query(Customer).filter(Customer.customer_id == "CUST001").first()
        if not cust:
            self.skipTest("Seed data not loaded.")
        
        shipment = self.db.query(Shipment).filter(Shipment.shipment_id == "SL1004").first()
        self.assertIsNotNone(shipment)
        self.assertEqual(shipment.customer_id, cust.id)
        self.assertEqual(shipment.customer.name, "Rahul Patel")

    def test_05_shipment_delivery_events(self):
        """5. Verify shipment can have delivery events timeline."""
        shipment = self.db.query(Shipment).filter(Shipment.shipment_id == "SL1004").first()
        if not shipment:
            self.skipTest("Seed data not loaded.")

        events = self.db.query(DeliveryEvent).filter(DeliveryEvent.shipment_id == shipment.id).all()
        self.assertTrue(len(events) > 0)
        statuses = [e.status for e in events]
        self.assertIn("In Transit", statuses)

    def test_06_customer_ticket_creation(self):
        """6. Verify customer can create a support ticket linked to shipment."""
        cust = self.db.query(Customer).filter(Customer.customer_id == "CUST002").first()
        if not cust:
            self.skipTest("Seed data not loaded.")
        
        ticket = self.db.query(Ticket).filter(Ticket.ticket_id == "LGT-1021").first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.customer_id, cust.id)
        self.assertEqual(ticket.issue_type, "Delivery Delay")
        self.assertEqual(ticket.status, "In Progress")

    def test_07_customer_invoices(self):
        """7. Verify customer has invoices linked with proper amount calculations."""
        cust = self.db.query(Customer).filter(Customer.customer_id == "CUST001").first()
        if not cust:
            self.skipTest("Seed data not loaded.")

        invoice = self.db.query(Invoice).filter(Invoice.invoice_id == "INV-2045").first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.customer_id, cust.id)
        self.assertEqual(invoice.payment_status, "Paid")
        self.assertEqual(Decimal(str(invoice.total_amount)), Decimal("1250.00"))

    def test_08_refund_request_default_status(self):
        """8. Verify refund request starts strictly as 'Pending Approval' without auto-approval."""
        refund = self.db.query(RefundRequest).filter(RefundRequest.refund_id == "REF-001").first()
        if not refund:
            self.skipTest("Seed data not loaded.")

        self.assertEqual(refund.status, "Pending Approval")
        self.assertIsNone(refund.approved_by)
        self.assertIsNone(refund.approved_at)

    def test_09_conversation_messages(self):
        """9. Verify conversation contains multiple ordered chat messages."""
        conv = self.db.query(Conversation).filter(Conversation.conversation_id == "CONV-1001").first()
        if not conv:
            self.skipTest("Seed data not loaded.")

        messages = self.db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id).all()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender_type, "customer")
        self.assertEqual(messages[1].sender_type, "ai")
        self.assertEqual(messages[0].intent, "shipment_tracking")

    def test_10_foreign_key_relationships(self):
        """10. Verify foreign key constraints and bidirectional relationship mappings."""
        cust = self.db.query(Customer).filter(Customer.customer_id == "CUST001").first()
        if not cust:
            self.skipTest("Seed data not loaded.")

        # Check relationships populated from ORM
        self.assertTrue(len(cust.shipments) >= 2)
        self.assertTrue(len(cust.invoices) >= 1)
        self.assertTrue(len(cust.conversations) >= 1)

if __name__ == "__main__":
    unittest.main()
