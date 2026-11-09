import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str):
    ADMIN = "Admin"
    MANAGER = "Manager"
    OUTGOING_MEMBER = "Outgoing Member"
    INCOMING_MEMBER = "Incoming Member"


class KnowledgeStatus(str):
    DRAFT = "DRAFT"
    NEEDS_REVIEW = "NEEDS REVIEW"
    SUPPORTED = "SUPPORTED"
    CONFLICTING = "CONFLICTING"
    MISSING_EVIDENCE = "MISSING EVIDENCE"
    UNRESOLVED = "UNRESOLVED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.INCOMING_MEMBER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    created_projects = relationship("Project", back_populates="creator")
    project_memberships = relationship("ProjectMember", back_populates="user")
    uploaded_documents = relationship("Document", back_populates="uploader")
    reviews = relationship("KnowledgeItem", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="created_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    knowledge_items = relationship("KnowledgeItem", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("TaskItem", back_populates="project", cascade="all, delete-orphan")
    gaps = relationship("KnowledgeGap", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default=UserRole.INCOMING_MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)  # in bytes
    page_count = Column(Integer, default=1)
    processing_status = Column(String(50), default="PENDING")  # PENDING, PROCESSING, PROCESSED, FAILED
    raw_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    knowledge_items = relationship("KnowledgeItem", back_populates="document", cascade="all, delete-orphan")
    evidence_records = relationship("Evidence", back_populates="document", cascade="all, delete-orphan")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    type = Column(String(50), nullable=False)
    # technical_decision, pending_task, unresolved_bug, project_risk, dependency, task_ownership, context, tech_stack, architecture
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    status = Column(String(50), default=KnowledgeStatus.DRAFT)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="knowledge_items")
    document = relationship("Document", back_populates="knowledge_items")
    reviewer = relationship("User", back_populates="reviews")
    evidence = relationship("Evidence", back_populates="knowledge_item", uselist=False, cascade="all, delete-orphan")
    task_details = relationship("TaskItem", back_populates="knowledge_item", uselist=False, cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, default=1)
    source_location = Column(String(255), nullable=True)
    exact_quote = Column(Text, nullable=False)
    match_confidence = Column(Float, default=1.0)
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    knowledge_item = relationship("KnowledgeItem", back_populates="evidence")
    document = relationship("Document", back_populates="evidence_records")


class TaskItem(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String(255), nullable=True)
    deadline = Column(String(100), nullable=True)
    priority = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    knowledge_item = relationship("KnowledgeItem", back_populates="task_details")


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    gap_type = Column(String(50), nullable=False)
    # missing_owner, conflicting_deadline, unresolved_bug, missing_dependency, unverified_decision, missing_docs
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    item_id_1 = Column(Integer, ForeignKey("knowledge_items.id"), nullable=True)
    item_id_2 = Column(Integer, ForeignKey("knowledge_items.id"), nullable=True)
    status = Column(String(50), default="OPEN")  # OPEN, RESOLVED, DISMISSED
    suggested_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="gaps")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # project, document, knowledge_item, gap, report
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
