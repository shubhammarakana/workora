from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.customer import Customer
from ..auth import get_optional_current_user
from ..services.ai_manager_service import AIManagerService

router = APIRouter(prefix="/api/ai-manager", tags=["AI Manager / Orchestrator"])

class AIManagerChatRequest(BaseModel):
    message: str = Field(..., example="Where is SL1004?")
    session_id: Optional[str] = Field("demo-session-001", example="demo-session-001")
    selected_employee: Optional[str] = Field(None, example="shipment")

class AIRouteRequest(BaseModel):
    message: str = Field(..., example="I want ₹2,000 refund for SL1004")
    selected_employee: Optional[str] = None

class AIExecuteRequest(BaseModel):
    message: str = Field(..., example="My shipment SL1003 is delayed and I want a refund.")
    session_id: Optional[str] = "demo-session-001"

@router.post("/chat", summary="AI Manager Central Orchestration Chat")
def ai_manager_chat(
    req: AIManagerChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Central orchestration chat endpoint. Receives customer message, detects intent,
    extracts entities, routes/coordinates AI employees, enforces policy checks & human approval.
    """
    return AIManagerService.orchestrate_request(
        message=req.message,
        db=db,
        session_id=req.session_id or "demo-session-001",
        selected_employee=req.selected_employee,
        current_user=current_user
    )

@router.post("/route", summary="Get Internal AI Manager Routing Decision")
def get_routing_decision(
    req: AIRouteRequest
):
    """
    Returns the internal routing decision object (intent, shipment_id, selected employee, confidence score).
    """
    entities = AIManagerService.extract_entities(req.message)
    classification = AIManagerService.classify_intent(req.message, req.selected_employee)

    return {
        "intent": classification["intent"],
        "shipment_id": entities.get("shipment_id"),
        "invoice_id": entities.get("invoice_id"),
        "amount": entities.get("amount"),
        "employee": classification["employee"],
        "confidence": classification["confidence"],
        "requires_approval": classification["requires_approval"],
        "label": "Demo Data"
    }

@router.get("/status", summary="Get AI Manager Online Status & Activity Stats")
def get_manager_status(
    db: Session = Depends(get_db)
):
    """
    Returns AI Manager status, online health, and demo statistics.
    """
    return AIManagerService.get_manager_status(db)

@router.post("/execute", summary="Execute Multi-Employee Sequential Pipeline")
def execute_multi_employee_pipeline(
    req: AIExecuteRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Executes multi-employee workflow sequentially (e.g. Shipment Check -> Billing Refund -> Human Approval).
    """
    return AIManagerService.orchestrate_request(
        message=req.message,
        db=db,
        session_id=req.session_id or "demo-session-001",
        current_user=current_user
    )
