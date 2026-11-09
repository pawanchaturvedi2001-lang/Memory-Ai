from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    KnowledgeItem, Evidence, TaskItem, KnowledgeGap,
    Project, User, UserRole, KnowledgeStatus, AuditLog
)
from app.schemas.schemas import (
    KnowledgeItemResponse, KnowledgeItemCreate, KnowledgeItemUpdate,
    KnowledgeGapResponse, TaskItemResponse, EvidenceResponse
)
from app.security.auth import get_current_user, require_roles
from app.services.evidence_service import EvidenceService
from app.services.gap_detection import GapDetectionService

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


def format_knowledge_response(k: KnowledgeItem, db: Session) -> KnowledgeItemResponse:
    res = KnowledgeItemResponse.model_validate(k)
    if k.document:
        res.document_filename = k.document.filename
    if k.evidence:
        res.evidence = EvidenceResponse.model_validate(k.evidence)
        if k.document:
            res.evidence.document_filename = k.document.filename
    if k.task_details:
        res.task_details = TaskItemResponse.model_validate(k.task_details)
    return res


@router.get("/{project_id}", response_model=List[KnowledgeItemResponse])
def get_project_knowledge(
    project_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(KnowledgeItem).filter(KnowledgeItem.project_id == project_id)

    # Role-based filtering: Incoming Members should only see APPROVED items or items deemed safe/published
    if current_user.role == UserRole.INCOMING_MEMBER:
        query = query.filter(KnowledgeItem.status.in_([KnowledgeStatus.APPROVED, KnowledgeStatus.SUPPORTED]))

    if status_filter:
        query = query.filter(KnowledgeItem.status == status_filter)
    if type_filter:
        query = query.filter(KnowledgeItem.type == type_filter)

    items = query.order_by(KnowledgeItem.created_at.desc()).all()
    return [format_knowledge_response(k, db) for k in items]


@router.get("/item/{item_id}", response_model=KnowledgeItemResponse)
def get_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    return format_knowledge_response(item, db)


@router.post("/{project_id}", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_item(
    project_id: int,
    item_in: KnowledgeItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    item = KnowledgeItem(
        project_id=project_id,
        document_id=item_in.document_id,
        type=item_in.type,
        title=item_in.title,
        content=item_in.content,
        confidence=item_in.confidence,
        status=item_in.status or KnowledgeStatus.NEEDS_REVIEW
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    if item_in.evidence_quote and item_in.document_id:
        doc = db.query(Project).filter(Project.id == item_in.document_id).first()
        if doc:
            EvidenceService.create_evidence_record(
                db=db,
                knowledge_item_id=item.id,
                document=doc,
                exact_quote=item_in.evidence_quote,
                page_number=item_in.evidence_page or 1
            )

    GapDetectionService.run_gap_analysis(project_id, db)
    return format_knowledge_response(item, db)


@router.put("/item/{item_id}", response_model=KnowledgeItemResponse)
def update_knowledge_item(
    item_id: int,
    item_update: KnowledgeItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.OUTGOING_MEMBER]))
):
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    if item_update.title is not None:
        item.title = item_update.title
    if item_update.content is not None:
        item.content = item_update.content
    if item_update.type is not None:
        item.type = item_update.type
    if item_update.status is not None:
        item.status = item_update.status
    if item_update.review_comment is not None:
        item.review_comment = item_update.review_comment

    db.commit()
    db.refresh(item)

    # Re-run gap analysis
    GapDetectionService.run_gap_analysis(item.project_id, db)

    return format_knowledge_response(item, db)


@router.delete("/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    project_id = item.project_id
    db.delete(item)
    db.commit()

    GapDetectionService.run_gap_analysis(project_id, db)
    return None


@router.get("/{project_id}/gaps", response_model=List[KnowledgeGapResponse])
def get_project_gaps(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    gaps = db.query(KnowledgeGap).filter(
        KnowledgeGap.project_id == project_id
    ).order_by(KnowledgeGap.created_at.desc()).all()
    return gaps


@router.post("/{project_id}/analyze-gaps", response_model=List[KnowledgeGapResponse])
def trigger_gap_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.OUTGOING_MEMBER]))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    gaps = GapDetectionService.run_gap_analysis(project_id, db)
    return gaps
