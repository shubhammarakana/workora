# LOGIFLOW LOGISTICS · Workora AI Workforce

> **Workora is not just a chatbot — it is an AI workforce for logistics.**  
> *"AI Employees. Real Work. Better Business."* Central Orchestration · Policy Enforcement · Human Approval Workflows · Immutable Audit Logs

---

## 📸 Application Preview

![LogiFlow Logistics AI Workforce Dashboard](screenshots/dashboard.png)

---

## 🌟 Key Highlights

- **Virtual AI Workforce Office (2.5D Interactive View)**: Real-time visibility into AI employee workstations, tasks, and system states.
- **Dedicated AI Employees**:
  - 🧠 **AI Manager / Orchestrator**: Central intent classifier, task dispatcher, and multi-agent coordinator.
  - 🎧 **Customer Service Employee**: Handles complaints, inquiries, ticket triage, and human handoff.
  - 📦 **Shipment Employee**: Live tracking status, milestones, origin/destination updates, and delivery timelines.
  - 🚚 **Delivery Employee**: Slot scheduling, dynamic address modifications, and dispatch management.
  - 📄 **Billing Employee**: Invoice lookups, dispute processing, and refund request generation with human-in-the-loop policies.
- **Human Approval Security Center**: Sensitive actions (e.g. refunds, address changes, SLA breach escalations) require human operator sign-off before execution.
- **Full-Stack Architecture**: React/Tailwind frontend paired with a high-performance FastAPI and SQLAlchemy backend.

---

## 📁 Repository Structure

```text
WORKORA/
├── index.html               # Main frontend interface & 2.5D AI Workforce Dashboard
├── screenshots/
│   └── dashboard.png        # Application dashboard preview
├── backend/
│   ├── alembic/             # Database schema migrations
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── routes/          # FastAPI REST endpoints
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/        # AI business logic & orchestration
│   │   ├── database.py      # Database engine & session config
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # Backend test suites & verification
│   ├── requirements.txt     # Python backend dependencies
│   └── README.md            # Detailed backend documentation
└── src/                     # Shared frontend types and mock logistics data
```

---

## 🚀 Quick Start Guide

### 1. Frontend Setup
Simply open `index.html` in any modern web browser or serve it with a local static server:

```bash
# Using Python
python -m http.server 5500

# Or with Node
npx serve .
```
Then navigate to `http://localhost:5500`.

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate     # On Windows
# source venv/bin/activate # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Seed sample data & run server
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

---

## 🛡️ License
Private & Proprietary - All rights reserved.
