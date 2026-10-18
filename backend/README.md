# LogiFlow Logistics Database & Backend API

> **Powered by Workora AI Employee**  
> Complete Relational Database Architecture & REST API Backend for the LogiFlow Logistics Platform.

---

## 🏗️ 1. Database Architecture & Schema

The relational database (`logiflow_db`) is designed for enterprise logistics scalability, supporting customers, shipments, real-time tracking events, delivery assignments, support tickets, billing invoices, human-gated refund approvals, customer chat sessions, and knowledge documents.

### 📐 Entity Relationship Diagram

```
customers
    │
    ├──< shipments
    │       │
    │       ├──< delivery_events
    │       │
    │       └──< delivery_assignments
    │
    ├──< tickets
    │
    ├──< invoices
    │       │
    │       └──< refund_requests
    │
    ├──< refund_requests
    │
    └──< conversations
              │
              └──< chat_messages

knowledge_documents (Standalone RAG / Knowledge Base)
audit_logs (Centralized System & Action Auditing)
```

---

## 🗄️ 2. Tables & Schema Specifications

| Table | Primary Key | Key Foreign Keys & Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `customers` | `id` (BIGINT) | `customer_id` (UQ), `email` (UQ), `phone` (UQ) | Customer identity, profile & credentials |
| `shipments` | `id` (BIGINT) | `shipment_id` (UQ), `customer_id` (FK), `tracking_number` (UQ), `status` (IX) | Package status, location, origin & ETA |
| `delivery_events` | `id` (BIGINT) | `shipment_id` (FK) | Granular tracking timeline milestone events |
| `delivery_assignments` | `id` (BIGINT) | `shipment_id` (FK) | Driver, vehicle and route allocations |
| `tickets` | `id` (BIGINT) | `ticket_id` (UQ), `customer_id` (FK), `shipment_id` (FK), `status` (IX) | Customer support inquiries and resolutions |
| `invoices` | `id` (BIGINT) | `invoice_id` (UQ), `customer_id` (FK), `shipment_id` (FK) | Billing, line items, taxes & payment status |
| `refund_requests` | `id` (BIGINT) | `refund_id` (UQ), `customer_id` (FK), `shipment_id` (FK), `status` (IX) | Human-approval gated refund processing |
| `conversations` | `id` (BIGINT) | `conversation_id` (UQ), `customer_id` (FK) | Chat sessions across web/WhatsApp channels |
| `chat_messages` | `id` (BIGINT) | `conversation_id` (FK) | Individual chat turns with extracted intents |
| `knowledge_documents` | `id` (BIGINT) | `document_id` (UQ) | Company policies and delivery SLAs for AI RAG |
| `audit_logs` | `id` (BIGINT) | `customer_id` (FK) | Tamper-evident logging of tracking and actions |

---

## 🚀 3. Quick Start & Execution

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/logiflow_db
SECRET_KEY=workora_logiflow_jwt_secret_key_2026
FRONTEND_URL=http://localhost:3000
```
*(Defaults to SQLite `sqlite:///./logiflow.db` automatically when PostgreSQL is not running locally).*

### 3. Database Migrations (Alembic)
Run migrations to generate all tables and indexes:
```bash
alembic upgrade head
```

### 4. Seed Fictional Demo Data
Seed realistic demo customers, shipments, delivery events, tickets, and invoices:
```bash
python -m app.seed
```

### 5. Run Database Test Suite
Run the 10-point comprehensive database verification test suite:
```bash
python tests/test_database.py
```

### 6. Start FastAPI Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔒 4. Security & Isolation Rules

- **Zero Plain-Text Passwords**: All passwords are salted and hashed with HMAC-SHA256 (`password_hash`).
- **Data Isolation**: Customers can only view and interact with their own shipments, invoices, and tickets.
- **Refund Gatekeeping**: Refund requests strictly default to `Pending Approval` and require human reviewer confirmation.
- **ORM Parameterization**: All SQL queries execute through SQLAlchemy ORM parameterization to eliminate SQL injection risks.
- **Fictional Prototype Data**: All names, tracking IDs, and credentials are intentionally fictional.
