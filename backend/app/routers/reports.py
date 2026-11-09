from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Project, KnowledgeItem, TaskItem, KnowledgeGap, Document, AuditLog
from app.security.auth import get_current_user
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{project_id}")
def get_report_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs = db.query(Document).filter(Document.project_id == project_id).all()
    items = db.query(KnowledgeItem).filter(KnowledgeItem.project_id == project_id).all()
    tasks = db.query(TaskItem).filter(TaskItem.project_id == project_id).all()
    gaps = db.query(KnowledgeGap).filter(KnowledgeGap.project_id == project_id).all()

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at
        },
        "statistics": {
            "documents_count": len(docs),
            "knowledge_items_count": len(items),
            "tasks_count": len(tasks),
            "gaps_count": len(gaps),
            "approved_count": len([i for i in items if i.status == "APPROVED"]),
            "needs_review_count": len([i for i in items if i.status in ["NEEDS REVIEW", "DRAFT", "SUPPORTED"]])
        },
        "sections": {
            "tech_stack": [i for i in items if i.type == "tech_stack"],
            "technical_decisions": [i for i in items if i.type == "technical_decision"],
            "pending_tasks": tasks,
            "unresolved_bugs": [i for i in items if i.type == "unresolved_bug"],
            "dependencies": [i for i in items if i.type == "dependency"],
            "risks": [i for i in items if i.type == "project_risk"],
            "knowledge_gaps": gaps
        }
    }


@router.get("/{project_id}/download")
def download_handover_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pdf_buffer = ReportService.generate_pdf_handover_report(project_id, db)
    pdf_bytes = pdf_buffer.getvalue()

    filename = f"MemoryAI_Handover_{project.name.replace(' ', '_')}_{project_id}.pdf"

    # Audit log
    audit = AuditLog(
        project_id=project_id,
        user_id=current_user.id,
        action="HANDOVER_REPORT_DOWNLOADED",
        entity_type="report",
        details=f"PDF Handover report generated and downloaded by {current_user.email}"
    )
    db.add(audit)
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
