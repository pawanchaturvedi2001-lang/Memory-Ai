import os
import datetime
from sqlalchemy.orm import Session

from app.models.models import (
    User, UserRole, Project, ProjectMember,
    Document, KnowledgeItem, TaskItem, Evidence, KnowledgeStatus, AuditLog
)
from app.security.auth import get_password_hash
from app.services.gap_detection import GapDetectionService
from app.config import settings


DEMO_PROJECT_OVERVIEW = """[DEMO DATA - SYNTHETIC]
Project: ApexCommerce - NextGen Enterprise E-Commerce Platform
Version: 2.4.0-RC1
Summary: ApexCommerce is a distributed multi-tenant e-commerce system supporting omni-channel order routing, real-time inventory management, and personalized checkout experiences.

Architecture Overview:
- Frontend: Single Page Application built with React and Tailwind CSS.
- Backend Core: Modular Python FastAPI microservices coordinating with an asynchronous task worker.
- Primary Database: PostgreSQL 15 for ACID transactional order and payment processing.
- Caching & Session Layer: Distributed Redis cluster for cart persistence and rate-limiting.
"""

DEMO_TECHNICAL_DECISIONS = """[DEMO DATA - SYNTHETIC]
Architecture Decision Records (ADRs):

- ADR-001: Adoption of PostgreSQL for Transactional Data
Decided to adopt PostgreSQL 15 as our primary relational store for order integrity, customer ledger, and transactional compliance.

- ADR-002: JWT Authentication with Refresh Token Rotation
Selected RS256/HS256 signed JWT tokens stored in HTTP-only cookies for cross-service authentication.

- ADR-003: Stripe Elements for Global Checkout Integration
Decided to implement Stripe Elements for PCI-DSS compliant credit card and local payment method tokenization.
"""

DEMO_MEETING_NOTES_AND_TASKS = """[DEMO DATA - SYNTHETIC]
Sprint 42 Architecture Handover & Operations Meeting Notes
Attendees: Lead Architect (Outgoing), Engineering Manager, Senior Fullstack Dev

Action Items & Pending Tasks:
- Implement Stripe Webhook idempotency handler: Assigned to Sarah Jenkins. Deadline: 2026-11-20. Priority: HIGH.
- Checkout Service Performance Optimization: Assigned to Sarah Jenkins. Target Deadline: 2026-11-15. Priority: CRITICAL.
- Checkout Service Performance Optimization: Assigned to Alex Rivera. Target Deadline: 2026-12-05. Priority: HIGH.
- Optimize Redis cart session TTL: Owner: null. Deadline: 2026-11-28. Priority: MEDIUM.
- Configure Algolia Search Index Replication: Assigned to Marcus Vance. Deadline: null. Priority: MEDIUM.
"""

DEMO_BUG_REPORTS = """[DEMO DATA - SYNTHETIC]
Active Incident & Defect Log:

- BUG-1082: Checkout 500 Error on Zero-Decimal Currencies (JPY, KRW)
Severity: CRITICAL
Status: UNRESOLVED
Description: Customers paying in Japanese Yen experience a 500 Internal Server Error during calculation due to unexpected decimal conversion in currency helper module.

- BUG-1094: Broken Address Autocomplete in Safari Mobile
Severity: MEDIUM
Status: IN_PROGRESS
Description: Safari iOS occasionally fails to trigger geolocation dropdown on address form.
"""

DEMO_DEPENDENCIES_AND_GAPS = """[DEMO DATA - SYNTHETIC]
External Dependencies & Integrations:

- SendGrid Transactional Email API: Integrated and verified.
- Stripe Payment Gateway: Integrated in sandbox.
- Redis Cluster: Active in staging.
- ShipStation Logistics API: Unconfigured and missing sandbox API credentials in secrets vault. Requires engineering lead setup.
"""


def seed_demo_data(db: Session) -> Project:
    """
    Seeds the fictional E-Commerce Management System with the exact required synthetic issues:
    1. One task without an owner ('Optimize Redis cart session TTL')
    2. Two conflicting deadlines for the same task ('Checkout Service Performance Optimization': 2026-11-15 vs 2026-12-05)
    3. One unresolved bug ('BUG-1082: Checkout 500 Error on Zero-Decimal Currencies')
    4. One missing dependency ('ShipStation Logistics API: Unconfigured and missing credentials')
    5. One decision without supporting evidence ('ADR-004: In-Memory Message Bus Selection')
    """
    # 1. Ensure Default Demo Users exist across all 4 roles
    users_def = [
        {"email": "admin@memoryai.io", "name": "Elena Rostova (Admin)", "role": UserRole.ADMIN, "pwd": "password123"},
        {"email": "manager@memoryai.io", "name": "David Sterling (Manager)", "role": UserRole.MANAGER, "pwd": "password123"},
        {"email": "outgoing@memoryai.io", "name": "Sarah Jenkins (Outgoing Lead)", "role": UserRole.OUTGOING_MEMBER, "pwd": "password123"},
        {"email": "incoming@memoryai.io", "name": "Alex Rivera (Incoming Dev)", "role": UserRole.INCOMING_MEMBER, "pwd": "password123"}
    ]

    user_map = {}
    for u in users_def:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            user = User(
                email=u["email"],
                full_name=u["name"],
                role=u["role"],
                hashed_password=get_password_hash(u["pwd"]),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_map[u["role"]] = user
        else:
            user_map[u["role"]] = existing

    admin_user = user_map[UserRole.ADMIN]
    outgoing_user = user_map[UserRole.OUTGOING_MEMBER]
    incoming_user = user_map[UserRole.INCOMING_MEMBER]

    # 2. Check if demo project already exists
    demo_proj = db.query(Project).filter(Project.name == "ApexCommerce E-Commerce Platform [DEMO]").first()
    if demo_proj:
        # Re-run gap analysis to ensure all gaps are detected
        GapDetectionService.run_gap_analysis(demo_proj.id, db)
        return demo_proj

    # 3. Create Demo Project
    project = Project(
        name="ApexCommerce E-Commerce Platform [DEMO]",
        description="Enterprise multi-tenant e-commerce platform with automated knowledge handover for incoming team continuity. [SYNTHETIC DEMO DATASET]",
        status="ACTIVE",
        created_by_id=outgoing_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 4. Add Members
    for role_name, usr in user_map.items():
        pm = ProjectMember(project_id=project.id, user_id=usr.id, role=role_name)
        db.add(pm)
    db.commit()

    # 5. Create Documents and write files to disk
    docs_payload = [
        ("ApexCommerce_Architecture_Overview.txt", DEMO_PROJECT_OVERVIEW, "txt"),
        ("ADR_Technical_Decisions.txt", DEMO_TECHNICAL_DECISIONS, "txt"),
        ("Sprint42_Handover_Meeting_Notes.txt", DEMO_MEETING_NOTES_AND_TASKS, "txt"),
        ("Bug_Log_And_Incidents.txt", DEMO_BUG_REPORTS, "txt"),
        ("External_Dependencies.txt", DEMO_DEPENDENCIES_AND_GAPS, "txt")
    ]

    created_docs = []
    for fname, content, ftype in docs_payload:
        fpath = os.path.join(settings.UPLOAD_DIR, f"demo_{fname}")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        doc = Document(
            project_id=project.id,
            uploaded_by_id=outgoing_user.id,
            filename=fname,
            file_path=fpath,
            file_type=ftype,
            file_size=len(content.encode('utf-8')),
            page_count=1,
            processing_status="PROCESSED",
            raw_text=content
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        created_docs.append(doc)

    doc_arch, doc_dec, doc_notes, doc_bugs, doc_deps = created_docs

    # 6. Extract / Create Grounded Knowledge Items with Evidence

    # (A) Tech Stack Items
    ts1 = KnowledgeItem(
        project_id=project.id,
        document_id=doc_arch.id,
        type="tech_stack",
        title="Frontend: React & Tailwind CSS",
        content="Single Page Application built with React and Tailwind CSS for responsive customer interfaces.",
        confidence=0.98,
        status=KnowledgeStatus.APPROVED
    )
    db.add(ts1)

    ts2 = KnowledgeItem(
        project_id=project.id,
        document_id=doc_arch.id,
        type="tech_stack",
        title="Backend: Python FastAPI",
        content="Modular Python FastAPI microservices coordinating with an asynchronous task worker.",
        confidence=0.98,
        status=KnowledgeStatus.APPROVED
    )
    db.add(ts2)
    db.commit()

    # (B) Technical Decisions
    td1 = KnowledgeItem(
        project_id=project.id,
        document_id=doc_dec.id,
        type="technical_decision",
        title="PostgreSQL 15 as Primary Relational Store",
        content="Decided to adopt PostgreSQL 15 as our primary relational store for order integrity, customer ledger, and transactional compliance.",
        confidence=0.95,
        status=KnowledgeStatus.APPROVED
    )
    db.add(td1)
    db.commit()
    db.refresh(td1)

    # Link Evidence to TD1 (Supported)
    ev1 = Evidence(
        knowledge_item_id=td1.id,
        document_id=doc_dec.id,
        page_number=1,
        source_location="ADR-001 Section",
        exact_quote="Decided to adopt PostgreSQL 15 as our primary relational store for order integrity, customer ledger, and transactional compliance.",
        match_confidence=1.0,
        is_verified=True,
        verification_notes="Verbatim match verified in ADR_Technical_Decisions.txt"
    )
    db.add(ev1)

    # Required Problem 5: One decision WITHOUT supporting evidence!
    td2 = KnowledgeItem(
        project_id=project.id,
        document_id=doc_dec.id,
        type="technical_decision",
        title="Adoption of ZeroMQ for Distributed IPC",
        content="Engineering decided in private discussions to migrate microservice IPC to ZeroMQ instead of HTTP REST.",
        confidence=0.45,
        status=KnowledgeStatus.MISSING_EVIDENCE
    )
    db.add(td2)
    db.commit()
    db.refresh(td2)

    ev2 = Evidence(
        knowledge_item_id=td2.id,
        document_id=doc_dec.id,
        page_number=1,
        source_location="Unverified Claim",
        exact_quote="ZeroMQ was chosen during watercooler chat without formal ADR record.",
        match_confidence=0.0,
        is_verified=False,
        verification_notes="Excerpt could NOT be located in any uploaded project document."
    )
    db.add(ev2)

    # (C) Tasks
    # Task 1: Normal task with owner & deadline
    t1_ki = KnowledgeItem(
        project_id=project.id,
        document_id=doc_notes.id,
        type="pending_task",
        title="Implement Stripe Webhook Idempotency Handler",
        content="Implement Stripe Webhook idempotency handler to prevent duplicate fulfillment upon network retries.",
        confidence=0.95,
        status=KnowledgeStatus.APPROVED
    )
    db.add(t1_ki)
    db.commit()
    db.refresh(t1_ki)

    t1 = TaskItem(
        project_id=project.id,
        knowledge_item_id=t1_ki.id,
        title="Implement Stripe Webhook idempotency handler",
        description="Assigned to Sarah Jenkins. Deadline: 2026-11-20. Priority: HIGH.",
        owner="Sarah Jenkins",
        deadline="2026-11-20",
        priority="HIGH",
        status="IN_PROGRESS"
    )
    db.add(t1)

    # Required Problem 2: Conflicting deadlines for same task area!
    # Task 2a
    t2a_ki = KnowledgeItem(
        project_id=project.id,
        document_id=doc_notes.id,
        type="pending_task",
        title="Checkout Service Performance Optimization (Nov Deadline)",
        content="Checkout Service Performance Optimization targeted for Nov 15 sprint release.",
        confidence=0.90,
        status=KnowledgeStatus.CONFLICTING
    )
    db.add(t2a_ki)
    db.commit()
    db.refresh(t2a_ki)

    t2a = TaskItem(
        project_id=project.id,
        knowledge_item_id=t2a_ki.id,
        title="Checkout Service Performance Optimization",
        description="Target Deadline: 2026-11-15. Priority: CRITICAL.",
        owner="Sarah Jenkins",
        deadline="2026-11-15",
        priority="CRITICAL",
        status="PENDING"
    )
    db.add(t2a)

    # Task 2b (Conflicting deadline!)
    t2b_ki = KnowledgeItem(
        project_id=project.id,
        document_id=doc_notes.id,
        type="pending_task",
        title="Checkout Service Performance Optimization (Dec Deadline)",
        content="Checkout Service Performance Optimization scheduled for Dec 05 handover milestone.",
        confidence=0.90,
        status=KnowledgeStatus.CONFLICTING
    )
    db.add(t2b_ki)
    db.commit()
    db.refresh(t2b_ki)

    t2b = TaskItem(
        project_id=project.id,
        knowledge_item_id=t2b_ki.id,
        title="Checkout Service Performance Optimization",
        description="Target Deadline: 2026-12-05. Priority: HIGH.",
        owner="Alex Rivera",
        deadline="2026-12-05",
        priority="HIGH",
        status="PENDING"
    )
    db.add(t2b)

    # Required Problem 1: One task WITHOUT an owner!
    t3_ki = KnowledgeItem(
        project_id=project.id,
        document_id=doc_notes.id,
        type="pending_task",
        title="Optimize Redis Cart Session TTL",
        content="Optimize Redis cart session TTL to purge expired guest cart memory leaks.",
        confidence=0.88,
        status=KnowledgeStatus.NEEDS_REVIEW
    )
    db.add(t3_ki)
    db.commit()
    db.refresh(t3_ki)

    t3 = TaskItem(
        project_id=project.id,
        knowledge_item_id=t3_ki.id,
        title="Optimize Redis cart session TTL",
        description="No designated owner found in sprint notes.",
        owner=None,  # MISSING OWNER!
        deadline="2026-11-28",
        priority="MEDIUM",
        status="PENDING"
    )
    db.add(t3)

    # (D) Required Problem 3: One UNRESOLVED critical bug!
    b1_ki = KnowledgeItem(
        project_id=project.id,
        document_id=doc_bugs.id,
        type="unresolved_bug",
        title="BUG-1082: Checkout 500 Error on Zero-Decimal Currencies",
        content="Customers paying in Japanese Yen (JPY) or Korean Won (KRW) experience 500 Internal Server Error during calculation due to unexpected decimal conversion in currency helper module.",
        confidence=0.99,
        status=KnowledgeStatus.UNRESOLVED
    )
    db.add(b1_ki)
    db.commit()
    db.refresh(b1_ki)

    ev_bug = Evidence(
        knowledge_item_id=b1_ki.id,
        document_id=doc_bugs.id,
        page_number=1,
        source_location="Active Incident Log",
        exact_quote="BUG-1082: Checkout 500 Error on Zero-Decimal Currencies (JPY, KRW) Status: UNRESOLVED",
        match_confidence=1.0,
        is_verified=True,
        verification_notes="Exact match found in Bug_Log_And_Incidents.txt"
    )
    db.add(ev_bug)

    # (E) Required Problem 4: One MISSING dependency!
    dep1 = KnowledgeItem(
        project_id=project.id,
        document_id=doc_deps.id,
        type="dependency",
        title="ShipStation Logistics API",
        content="ShipStation Logistics API: Unconfigured and missing sandbox API credentials in secrets vault. Requires engineering lead setup.",
        confidence=0.95,
        status=KnowledgeStatus.NEEDS_REVIEW
    )
    db.add(dep1)
    db.commit()

    # 7. Execute Knowledge Gap Detection
    GapDetectionService.run_gap_analysis(project.id, db)

    # 8. Add Audit Log
    audit = AuditLog(
        project_id=project.id,
        user_id=admin_user.id,
        action="DEMO_DATASET_INITIALIZED",
        entity_type="project",
        entity_id=project.id,
        details="Synthetic demo project seeded with all 5 intentional anomalies for hackathon demonstration."
    )
    db.add(audit)
    db.commit()

    return project
