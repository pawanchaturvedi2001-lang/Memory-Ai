import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Document, Project, User, KnowledgeItem, UserRole, AuditLog
from app.schemas.schemas import DocumentResponse
from app.security.auth import get_current_user, require_roles
from app.services.document_service import DocumentService
from app.services.ai_service import AIService
from app.services.gap_detection import GapDetectionService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    auto_extract: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Target project not found")

    # Save file and extract text
    doc = await DocumentService.save_and_extract(file, project_id, current_user, db)

    # Automatically extract knowledge and run gap analysis
    if auto_extract:
        AIService.process_document_knowledge(doc, db)
        GapDetectionService.run_gap_analysis(project_id, db)

    res = DocumentResponse.model_validate(doc)
    res.knowledge_count = db.query(KnowledgeItem).filter(KnowledgeItem.document_id == doc.id).count()
    return res


@router.get("/project/{project_id}", response_model=List[DocumentResponse])
def get_project_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs = db.query(Document).filter(Document.project_id == project_id).order_by(Document.created_at.desc()).all()
    results = []
    for d in docs:
        item = DocumentResponse.model_validate(d)
        item.knowledge_count = db.query(KnowledgeItem).filter(KnowledgeItem.document_id == d.id).count()
        results.append(item)
    return results


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    item = DocumentResponse.model_validate(doc)
    item.knowledge_count = db.query(KnowledgeItem).filter(KnowledgeItem.document_id == doc.id).count()
    return {
        "metadata": item,
        "raw_text": doc.raw_text
    }


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Clear previous knowledge extracted from this doc if re-processing
    db.query(KnowledgeItem).filter(KnowledgeItem.document_id == doc.id).delete()
    db.commit()

    AIService.process_document_knowledge(doc, db)
    GapDetectionService.run_gap_analysis(doc.project_id, db)

    item = DocumentResponse.model_validate(doc)
    item.knowledge_count = db.query(KnowledgeItem).filter(KnowledgeItem.document_id == doc.id).count()
    return item


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete physical file
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    project_id = doc.project_id
    audit = AuditLog(
        project_id=project_id,
        user_id=current_user.id,
        action="DOCUMENT_DELETED",
        entity_type="document",
        entity_id=doc.id,
        details=f"Document '{doc.filename}' deleted by {current_user.email}"
    )
    db.add(audit)
    db.delete(doc)
    db.commit()

    # Re-run gap analysis
    GapDetectionService.run_gap_analysis(project_id, db)
    return None
