from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..models.customer import Customer
from ..auth import get_optional_current_user, get_current_admin_user
from ..schemas.approval import (
    ApprovalCreate,
    ApprovalOut,
    ApprovalDecision,
    ApprovalStats
)
from ..services.approval_service import ApprovalService

router = APIRouter(prefix="/api/approvals", tags=["Human Approval System"])

@router.post("", response_model=ApprovalOut, summary="Create an Approval Request")
def create_approval(
    req: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_current_user)
):
    """
    Create a new approval request for sensitive AI actions (refund, cancellation, address change).
    """
    return ApprovalService.create_approval_request(req, db, current_user)

@router.get("", response_model=List[ApprovalOut], summary="List Approval Requests")
def list_approvals(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    List all approval requests filtered by status (Pending Approval, Approved, Rejected, All).
    """
    return ApprovalService.get_approvals(db, status_filter)

@router.get("/stats", response_model=ApprovalStats, summary="Get Human Approval KPI Stats")
def get_approval_stats(
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary statistics for human approvals.
    """
    return ApprovalService.get_stats(db)

@router.get("/history", response_model=List[ApprovalOut], summary="Get Approval History")
def get_approval_history(
    db: Session = Depends(get_db)
):
    """
    Get audit history of all reviewed approvals.
    """
    return ApprovalService.get_approvals(db, "all")

@router.get("/{approval_id}", response_model=ApprovalOut, summary="Get Approval Request Details")
def get_approval(
    approval_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific approval request.
    """
    return ApprovalService.get_approval_by_id(approval_id, db)

@router.post("/{approval_id}/approve", response_model=ApprovalOut, summary="Approve Action Request")
def approve_action(
    approval_id: str,
    decision: Optional[ApprovalDecision] = None,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(get_current_admin_user)
):
    """
    Approve a sensitive action request. Requires DB-verified admin permissions.
    Unauthenticated or customer accounts receive 401/403 Forbidden.
    """
    return ApprovalService.approve_request(
        approval_id=approval_id,
        db=db,
        is_admin=True,
        reviewer_name=admin_user.name or "LogiFlow Admin",
        decision=decision
    )

@router.post("/{approval_id}/reject", response_model=ApprovalOut, summary="Reject Action Request")
def reject_action(
    approval_id: str,
    decision: Optional[ApprovalDecision] = None,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(get_current_admin_user)
):
    """
    Reject a sensitive action request with reason. Requires DB-verified admin permissions.
    Unauthenticated or customer accounts receive 401/403 Forbidden.
    """
    return ApprovalService.reject_request(
        approval_id=approval_id,
        db=db,
        is_admin=True,
        reviewer_name=admin_user.name or "LogiFlow Admin",
        decision=decision
    )
