import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import KnowledgeItem, User, UserRole, KnowledgeStatus, AuditLog, Project
from app.schemas.schemas import KnowledgeItemResponse, KnowledgeApprovalRequest
from app.security.auth import get_current_user, require_roles
from app.routers.knowledge import format_knowledge_response
from app.services.gap_detection import GapDetectionService

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("", response_model=List[KnowledgeItemResponse])
def get_approvals(
    project_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.OUTGOING_MEMBER]))
):
    """
    Returns knowledge items awaiting approval or with specific review statuses.
    Accessible to Admins, Managers, and Outgoing Members.
    """
    query = db.query(KnowledgeItem)

    if project_id:
        query = query.filter(KnowledgeItem.project_id == project_id)

    if status_filter:
        query = query.filter(KnowledgeItem.status == status_filter)
    else:
        # Default: show items that need review or decision
        query = query.filter(KnowledgeItem.status.in_([
            KnowledgeStatus.NEEDS_REVIEW,
            KnowledgeStatus.DRAFT,
            KnowledgeStatus.SUPPORTED,
            KnowledgeStatus.CONFLICTING,
            KnowledgeStatus.MISSING_EVIDENCE,
            KnowledgeStatus.UNRESOLVED
        ]))

    items = query.order_by(KnowledgeItem.created_at.desc()).all()
    return [format_knowledge_response(k, db) for k in items]


@router.patch("/{item_id}", response_model=KnowledgeItemResponse)
def review_knowledge_item(
    item_id: int,
    approval_req: KnowledgeApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.OUTGOING_MEMBER]))
):
    """
    Approve, reject, or edit an item.
    Updates reviewer_id, review_comment, approved_at timestamp, and audit trail.
    """
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    action = approval_req.action.upper()
    if action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be 'APPROVE' or 'REJECT'")

    # Optional content or title editing during review
    if approval_req.edited_title:
        item.title = approval_req.edited_title
    if approval_req.edited_content:
        item.content = approval_req.edited_content

    now = datetime.datetime.utcnow()
    item.reviewer_id = current_user.id
    item.review_comment = approval_req.review_comment
    item.approved_at = now
    item.updated_at = now

    old_status = item.status
    if action == "APPROVE":
        item.status = KnowledgeStatus.APPROVED
    else:
        item.status = KnowledgeStatus.REJECTED

    db.commit()
    db.refresh(item)

    # Maintain strict audit history
    audit = AuditLog(
        project_id=item.project_id,
        user_id=current_user.id,
        action=f"KNOWLEDGE_ITEM_{action}D",
        entity_type="knowledge_item",
        entity_id=item.id,
        details=f"Item '{item.title}' status changed from '{old_status}' to '{item.status}' by {current_user.email}. Comment: {approval_req.review_comment or 'None'}"
    )
    db.add(audit)
    db.commit()

    # Re-evaluate gaps with updated approvals
    GapDetectionService.run_gap_analysis(item.project_id, db)

    return format_knowledge_response(item, db)
