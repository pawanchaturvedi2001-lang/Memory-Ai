from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import (
    Project, Document, KnowledgeItem, TaskItem,
    KnowledgeGap, AuditLog, KnowledgeStatus, User
)
from app.schemas.schemas import DashboardStats, AuditLogResponse
from app.security.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_projects = db.query(Project).count()
    total_documents = db.query(Document).count()
    total_knowledge_items = db.query(KnowledgeItem).count()

    pending_tasks = db.query(TaskItem).filter(
        TaskItem.status.in_(["PENDING", "IN_PROGRESS", "BLOCKED"])
    ).count()

    unresolved_issues = db.query(KnowledgeItem).filter(
        KnowledgeItem.type == "unresolved_bug",
        KnowledgeItem.status != KnowledgeStatus.APPROVED
    ).count()

    knowledge_gaps = db.query(KnowledgeGap).filter(
        KnowledgeGap.status == "OPEN"
    ).count()

    approved_items = db.query(KnowledgeItem).filter(
        KnowledgeItem.status == KnowledgeStatus.APPROVED
    ).count()

    rejected_items = db.query(KnowledgeItem).filter(
        KnowledgeItem.status == KnowledgeStatus.REJECTED
    ).count()

    needs_review_items = db.query(KnowledgeItem).filter(
        KnowledgeItem.status.in_([
            KnowledgeStatus.NEEDS_REVIEW,
            KnowledgeStatus.DRAFT,
            KnowledgeStatus.SUPPORTED,
            KnowledgeStatus.CONFLICTING,
            KnowledgeStatus.MISSING_EVIDENCE,
            KnowledgeStatus.UNRESOLVED
        ])
    ).count()

    recent_logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(10).all()

    formatted_logs = [AuditLogResponse.model_validate(l) for l in recent_logs]

    return DashboardStats(
        total_projects=total_projects,
        total_documents=total_documents,
        total_knowledge_items=total_knowledge_items,
        pending_tasks=pending_tasks,
        unresolved_issues=unresolved_issues,
        knowledge_gaps=knowledge_gaps,
        approved_items=approved_items,
        rejected_items=rejected_items,
        needs_review_items=needs_review_items,
        recent_activity=formatted_logs
    )
