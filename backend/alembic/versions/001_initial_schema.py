"""Initial logistics database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-07 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Customers Table
    op.create_table(
        'customers',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('customer_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_customers_customer_id', 'customers', ['customer_id'], unique=True)
    op.create_index('ix_customers_email', 'customers', ['email'], unique=True)
    op.create_index('ix_customers_phone', 'customers', ['phone'], unique=True)

    # 2. Shipments Table
    op.create_table(
        'shipments',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('shipment_id', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.BigInteger(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tracking_number', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_location', sa.String(length=255), nullable=True),
        sa.Column('origin', sa.String(length=255), nullable=True),
        sa.Column('destination', sa.String(length=255), nullable=True),
        sa.Column('expected_delivery', sa.Date(), nullable=True),
        sa.Column('actual_delivery', sa.Date(), nullable=True),
        sa.Column('package_type', sa.String(length=100), nullable=True),
        sa.Column('weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('shipping_charge', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_shipments_shipment_id', 'shipments', ['shipment_id'], unique=True)
    op.create_index('ix_shipments_customer_id', 'shipments', ['customer_id'], unique=False)
    op.create_index('ix_shipments_tracking_number', 'shipments', ['tracking_number'], unique=True)
    op.create_index('ix_shipments_status', 'shipments', ['status'], unique=False)

    # 3. Delivery Events Table
    op.create_table(
        'delivery_events',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('shipment_id', sa.BigInteger(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_time', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_delivery_events_shipment_id', 'delivery_events', ['shipment_id'], unique=False)

    # 4. Delivery Assignments Table
    op.create_table(
        'delivery_assignments',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('shipment_id', sa.BigInteger(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('driver_name', sa.String(length=150), nullable=True),
        sa.Column('driver_phone', sa.String(length=20), nullable=True),
        sa.Column('vehicle_number', sa.String(length=50), nullable=True),
        sa.Column('vehicle_type', sa.String(length=100), nullable=True),
        sa.Column('assignment_status', sa.String(length=50), server_default='Assigned', nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_delivery_assignments_shipment_id', 'delivery_assignments', ['shipment_id'], unique=False)

    # 5. Tickets Table
    op.create_table(
        'tickets',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('ticket_id', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.BigInteger(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shipment_id', sa.BigInteger(), sa.ForeignKey('shipments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('issue_type', sa.String(length=100), nullable=False),
        sa.Column('issue', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=30), server_default='Medium', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Open', nullable=False),
        sa.Column('assigned_to', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_tickets_ticket_id', 'tickets', ['ticket_id'], unique=True)
    op.create_index('ix_tickets_customer_id', 'tickets', ['customer_id'], unique=False)
    op.create_index('ix_tickets_shipment_id', 'tickets', ['shipment_id'], unique=False)
    op.create_index('ix_tickets_status', 'tickets', ['status'], unique=False)

    # 6. Invoices Table
    op.create_table(
        'invoices',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('invoice_id', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.BigInteger(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shipment_id', sa.BigInteger(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), server_default='0.0', nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_status', sa.String(length=50), server_default='Pending', nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_invoices_invoice_id', 'invoices', ['invoice_id'], unique=True)
    op.create_index('ix_invoices_customer_id', 'invoices', ['customer_id'], unique=False)
    op.create_index('ix_invoices_shipment_id', 'invoices', ['shipment_id'], unique=False)

    # 7. Refund Requests Table
    op.create_table(
        'refund_requests',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('refund_id', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.BigInteger(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shipment_id', sa.BigInteger(), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), sa.ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Pending Approval', nullable=False),
        sa.Column('approved_by', sa.String(length=150), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_refund_requests_refund_id', 'refund_requests', ['refund_id'], unique=True)
    op.create_index('ix_refund_requests_customer_id', 'refund_requests', ['customer_id'], unique=False)
    op.create_index('ix_refund_requests_status', 'refund_requests', ['status'], unique=False)

    # 8. Conversations Table
    op.create_table(
        'conversations',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.BigInteger(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('channel', sa.String(length=50), server_default='web', nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Active', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_conversations_conversation_id', 'conversations', ['conversation_id'], unique=True)
    op.create_index('ix_conversations_customer_id', 'conversations', ['customer_id'], unique=False)

    # 9. Chat Messages Table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.BigInteger(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_type', sa.String(length=30), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_chat_messages_conversation_id', 'chat_messages', ['conversation_id'], unique=False)

    # 10. Knowledge Documents Table
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_knowledge_documents_document_id', 'knowledge_documents', ['document_id'], unique=True)

    # 11. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('customer_id', sa.BigInteger(), sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('result', sa.String(length=50), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)
    )
    op.create_index('ix_audit_logs_customer_id', 'audit_logs', ['customer_id'], unique=False)

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('knowledge_documents')
    op.drop_table('chat_messages')
    op.drop_table('conversations')
    op.drop_table('refund_requests')
    op.drop_table('invoices')
    op.drop_table('tickets')
    op.drop_table('delivery_assignments')
    op.drop_table('delivery_events')
    op.drop_table('shipments')
    op.drop_table('customers')
