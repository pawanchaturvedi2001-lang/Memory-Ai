import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import (
    Project, ProjectMember, User, UserRole,
    Document, KnowledgeItem, KnowledgeGap, TaskItem, AuditLog
)
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectMemberCreate, ProjectMemberResponse, DashboardStats
)
from app.security.auth import get_current_user, require_roles

router = APIRouter(prefix="/projects", tags=["Projects"])


def enrich_project_response(project: Project, db: Session) -> ProjectResponse:
    res = ProjectResponse.model_validate(project)
    res.document_count = db.query(Document).filter(Document.project_id == project.id).count()
    res.knowledge_count = db.query(KnowledgeItem).filter(KnowledgeItem.project_id == project.id).count()
    res.gap_count = db.query(KnowledgeGap).filter(KnowledgeGap.project_id == project.id, KnowledgeGap.status == "OPEN").count()
    res.pending_tasks_count = db.query(TaskItem).filter(
        TaskItem.project_id == project.id,
        TaskItem.status.in_(["PENDING", "IN_PROGRESS"])
    ).count()
    return res


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        name=project_in.name,
        description=project_in.description,
        status=project_in.status,
        created_by_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Automatically add creator as a member with their current role
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=current_user.role
    )
    db.add(member)

    # Audit log
    audit = AuditLog(
        project_id=project.id,
        user_id=current_user.id,
        action="PROJECT_CREATED",
        entity_type="project",
        entity_id=project.id,
        details=f"Project '{project.name}' created by {current_user.email}"
    )
    db.add(audit)
    db.commit()

    return enrich_project_response(project, db)


@router.get("", response_model=List[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Admins see all projects; others see projects they are members of or created
    if current_user.role == UserRole.ADMIN:
        projects = db.query(Project).order_by(Project.created_at.desc()).all()
    else:
        # Projects where user is creator or member
        project_ids = db.query(ProjectMember.project_id).filter(ProjectMember.user_id == current_user.id).subquery()
        projects = db.query(Project).filter(
            (Project.created_by_id == current_user.id) | (Project.id.in_(project_ids))
        ).order_by(Project.created_at.desc()).all()

    return [enrich_project_response(p, db) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return enrich_project_response(project, db)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.status is not None:
        project.status = project_in.status

    db.commit()
    db.refresh(project)

    audit = AuditLog(
        project_id=project.id,
        user_id=current_user.id,
        action="PROJECT_UPDATED",
        entity_type="project",
        entity_id=project.id,
        details=f"Project '{project.name}' updated by {current_user.email}"
    )
    db.add(audit)
    db.commit()

    return enrich_project_response(project, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    audit = AuditLog(
        project_id=project.id,
        user_id=current_user.id,
        action="PROJECT_DELETED",
        entity_type="project",
        entity_id=project.id,
        details=f"Project '{project.name}' deleted by {current_user.email}"
    )
    db.add(audit)
    db.delete(project)
    db.commit()
    return None


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    project_id: int,
    member_in: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_to_add = db.query(User).filter(User.id == member_in.user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_in.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    member = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        role=member_in.role
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    audit = AuditLog(
        project_id=project_id,
        user_id=current_user.id,
        action="MEMBER_ADDED",
        entity_type="project_member",
        entity_id=member.id,
        details=f"User {user_to_add.email} added to project with role {member.role}"
    )
    db.add(audit)
    db.commit()

    return member


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this project")

    db.delete(member)
    db.commit()
    return None
