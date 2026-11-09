import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr, Field


# ----------------------
# USER & AUTH SCHEMAS
# ----------------------

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "Incoming Member"


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


# ----------------------
# PROJECT MEMBER SCHEMAS
# ----------------------

class ProjectMemberBase(BaseModel):
    user_id: int
    role: str = "Incoming Member"


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    joined_at: datetime.datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# ----------------------
# PROJECT SCHEMAS
# ----------------------

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_by_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    creator: Optional[UserResponse] = None
    members: List[ProjectMemberResponse] = []
    document_count: Optional[int] = 0
    knowledge_count: Optional[int] = 0
    gap_count: Optional[int] = 0
    pending_tasks_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ----------------------
# EVIDENCE SCHEMAS
# ----------------------

class EvidenceBase(BaseModel):
    document_id: int
    page_number: int = 1
    source_location: Optional[str] = None
    exact_quote: str
    match_confidence: float = 1.0
    is_verified: bool = False
    verification_notes: Optional[str] = None


class EvidenceResponse(EvidenceBase):
    id: int
    knowledge_item_id: int
    created_at: datetime.datetime
    document_filename: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------
# TASK ITEM SCHEMAS
# ----------------------

class TaskItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "PENDING"


class TaskItemCreate(TaskItemBase):
    project_id: int
    knowledge_item_id: Optional[int] = None


class TaskItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TaskItemResponse(TaskItemBase):
    id: int
    project_id: int
    knowledge_item_id: Optional[int] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ----------------------
# KNOWLEDGE ITEM SCHEMAS
# ----------------------

class KnowledgeItemBase(BaseModel):
    type: str  # technical_decision, pending_task, unresolved_bug, project_risk, dependency, task_ownership, context, tech_stack, architecture
    title: str
    content: str
    confidence: float = 1.0
    status: str = "DRAFT"  # DRAFT, NEEDS REVIEW, SUPPORTED, CONFLICTING, MISSING EVIDENCE, UNRESOLVED, APPROVED, REJECTED


class KnowledgeItemCreate(KnowledgeItemBase):
    project_id: int
    document_id: Optional[int] = None
    evidence_quote: Optional[str] = None
    evidence_page: Optional[int] = 1


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    review_comment: Optional[str] = None


class KnowledgeApprovalRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    review_comment: Optional[str] = None
    edited_content: Optional[str] = None
    edited_title: Optional[str] = None


class KnowledgeItemResponse(KnowledgeItemBase):
    id: int
    project_id: int
    document_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    review_comment: Optional[str] = None
    approved_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    evidence: Optional[EvidenceResponse] = None
    task_details: Optional[TaskItemResponse] = None
    reviewer: Optional[UserResponse] = None
    document_filename: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------
# KNOWLEDGE GAP SCHEMAS
# ----------------------

class KnowledgeGapBase(BaseModel):
    gap_type: str  # missing_owner, conflicting_deadline, unresolved_bug, missing_dependency, unverified_decision, missing_docs
    title: str
    description: str
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    status: str = "OPEN"  # OPEN, RESOLVED, DISMISSED
    suggested_action: Optional[str] = None
    item_id_1: Optional[int] = None
    item_id_2: Optional[int] = None


class KnowledgeGapCreate(KnowledgeGapBase):
    project_id: int


class KnowledgeGapResponse(KnowledgeGapBase):
    id: int
    project_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ----------------------
# DOCUMENT SCHEMAS
# ----------------------

class DocumentResponse(BaseModel):
    id: int
    project_id: int
    uploaded_by_id: int
    filename: str
    file_type: str
    file_size: int
    page_count: int
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime.datetime
    uploader: Optional[UserResponse] = None
    knowledge_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ----------------------
# AUDIT LOG SCHEMAS
# ----------------------

class AuditLogResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime.datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# ----------------------
# DASHBOARD STATS SCHEMAS
# ----------------------

class DashboardStats(BaseModel):
    total_projects: int
    total_documents: int
    total_knowledge_items: int
    pending_tasks: int
    unresolved_issues: int
    knowledge_gaps: int
    approved_items: int
    rejected_items: int
    needs_review_items: int
    recent_activity: List[AuditLogResponse] = []
