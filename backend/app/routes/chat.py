from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.customer import Customer
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService
from ..auth import get_optional_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse, summary="Process chat message with AI Logistics Assistant")
def process_chat_message(
    chat_req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Handles customer queries through Workora AI logistics logic.
    Detects intents (shipment tracking, delivery status, complaints, invoices, human support)
    and searches PostgreSQL for real-time status.
    """
    return ChatService.process_message(
        message=chat_req.message,
        db=db,
        current_user=current_user
    )
