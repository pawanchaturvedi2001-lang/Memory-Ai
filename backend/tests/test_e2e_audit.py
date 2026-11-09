import os
import sys
import io
import time
import asyncio
import httpx
import docx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import SessionLocal
from app.models.models import User, Project, Document, KnowledgeItem, KnowledgeGap, Evidence, TaskItem


def generate_sample_pdf() -> bytes:
    """Generates a valid binary PDF with test architectural decisions and bugs."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, "Project Architecture & System Specification")
    c.drawString(100, 720, "ADR-101: Decision: Adopted PostgreSQL for relational transaction persistence.")
    c.drawString(100, 690, "BUG-501: Critical checkout defect: Memory leak in worker process. Status: UNRESOLVED.")
    c.drawString(100, 660, "Task: Configure Redis Sentinel: Assigned to Marcus. Deadline: 2026-12-15. Priority: HIGH.")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def generate_sample_docx() -> bytes:
    """Generates a valid binary DOCX file with tasks and dependencies."""
    doc = docx.Document()
    doc.add_heading("Sprint Notes & Dependency Log", level=1)
    doc.add_paragraph("Action items from sprint review:")
    doc.add_paragraph("- Task: Migrate customer auth to OAuth2: Owner: null. Deadline: 2026-12-01. Priority: HIGH.")
    doc.add_paragraph("- Dependency: SendGrid API: Integration active in production.")
    doc.add_paragraph("- Dependency: Twilio SMS Gateway: Unconfigured and missing sandbox API key.")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def generate_sample_txt() -> bytes:
    """Generates a plain text file with conflicting deadlines."""
    content = (
        "## Release Milestones & Conflicting Deadlines\n"
        "- Task: Upgrade Elasticsearch Cluster: Assigned to Alex. Deadline: 2026-11-20. Priority: CRITICAL.\n"
        "- Task: Upgrade Elasticsearch Cluster: Assigned to Sarah. Deadline: 2026-12-10. Priority: HIGH.\n"
        "- Decision: We chose FastAPI for REST services.\n"
    )
    return content.encode("utf-8")


async def run_full_audit():
    ts = int(time.time())
    admin_email = f"audit_admin_{ts}@memoryai.io"
    incoming_email = f"audit_incoming_{ts}@memoryai.io"

    print("=================================================================")
    print(" STARTING FINAL END-TO-END AUDIT OF PROJECT MEMORY AI")
    print("=================================================================\n")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # -------------------------------------------------------------
        # 1. USER REGISTRATION AND LOGIN (JWT)
        # -------------------------------------------------------------
        print("[TEST 1/12] User Registration & JWT Authentication...")
        reg_res = await client.post("/api/auth/register", json={
            "email": admin_email,
            "password": "auditpassword123",
            "full_name": "Audit Administrator",
            "role": "Admin"
        })
        assert reg_res.status_code == 201, f"Admin reg failed: {reg_res.text}"
        admin_token = reg_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("  [OK] Admin registered and JWT issued")

        # Register Incoming Member for RBAC test
        in_res = await client.post("/api/auth/register", json={
            "email": incoming_email,
            "password": "auditpassword123",
            "full_name": "Audit Incoming Dev",
            "role": "Incoming Member"
        })
        assert in_res.status_code == 201, f"Incoming reg failed: {in_res.text}"
        incoming_token = in_res.json()["access_token"]
        incoming_headers = {"Authorization": f"Bearer {incoming_token}"}
        print("  [OK] Incoming Member registered and JWT issued")

        # Login test
        login_res = await client.post("/api/auth/login", json={
            "email": admin_email,
            "password": "auditpassword123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        assert "access_token" in login_res.json()
        print("  [OK] Login endpoint verified")

        # -------------------------------------------------------------
        # 2. PROJECT CREATION
        # -------------------------------------------------------------
        print("\n[TEST 2/12] Project Creation...")
        proj_res = await client.post("/api/projects", json={
            "name": "Audit Handover System Alpha",
            "description": "Comprehensive end-to-end verification project",
            "status": "ACTIVE"
        }, headers=admin_headers)
        assert proj_res.status_code == 201, f"Project creation failed: {proj_res.text}"
        project_id = proj_res.json()["id"]
        print(f"  [OK] Project created with ID: {project_id}")

        # Add incoming dev as project member
        member_res = await client.post(f"/api/projects/{project_id}/members", json={
            "user_id": in_res.json()["user"]["id"],
            "role": "Incoming Member"
        }, headers=admin_headers)
        assert member_res.status_code == 200, f"Add member failed: {member_res.text}"
        print("  [OK] Project member assigned")

        # -------------------------------------------------------------
        # 3 & 4. UPLOADS (PDF, DOCX, TXT) AND TEXT EXTRACTION
        # -------------------------------------------------------------
        print("\n[TEST 3-4/12] PDF, DOCX, and TXT Uploads & Text Extraction...")

        # (A) Upload PDF
        pdf_bytes = generate_sample_pdf()
        pdf_res = await client.post(
            "/api/documents/upload",
            data={"project_id": str(project_id), "auto_extract": "true"},
            files={"file": ("architecture_spec.pdf", pdf_bytes, "application/pdf")},
            headers=admin_headers
        )
        assert pdf_res.status_code == 201, f"PDF upload failed: {pdf_res.text}"
        doc_pdf_id = pdf_res.json()["id"]
        print(f"  [OK] PDF uploaded & extracted ({len(pdf_bytes)} bytes, doc ID: {doc_pdf_id})")

        # (B) Upload DOCX
        docx_bytes = generate_sample_docx()
        docx_res = await client.post(
            "/api/documents/upload",
            data={"project_id": str(project_id), "auto_extract": "true"},
            files={"file": ("sprint_dependencies.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=admin_headers
        )
        assert docx_res.status_code == 201, f"DOCX upload failed: {docx_res.text}"
        doc_docx_id = docx_res.json()["id"]
        print(f"  [OK] DOCX uploaded & extracted ({len(docx_bytes)} bytes, doc ID: {doc_docx_id})")

        # (C) Upload TXT
        txt_bytes = generate_sample_txt()
        txt_res = await client.post(
            "/api/documents/upload",
            data={"project_id": str(project_id), "auto_extract": "true"},
            files={"file": ("milestones_conflicts.txt", txt_bytes, "text/plain")},
            headers=admin_headers
        )
        assert txt_res.status_code == 201, f"TXT upload failed: {txt_res.text}"
        doc_txt_id = txt_res.json()["id"]
        print(f"  [OK] TXT uploaded & extracted ({len(txt_bytes)} bytes, doc ID: {doc_txt_id})")

        # -------------------------------------------------------------
        # 5 & 6. AI KNOWLEDGE EXTRACTION & CATEGORIES
        # -------------------------------------------------------------
        print("\n[TEST 5-6/12] Knowledge Extraction & Multi-Category Identification...")
        k_res = await client.get(f"/api/knowledge/{project_id}", headers=admin_headers)
        assert k_res.status_code == 200
        extracted_items = k_res.json()
        print(f"  [OK] Total knowledge items extracted: {len(extracted_items)}")
        assert len(extracted_items) >= 4, f"Expected at least 4 items, got {len(extracted_items)}"

        types_found = {item["type"] for item in extracted_items}
        print(f"  [OK] Knowledge types identified: {', '.join(types_found)}")
        assert "technical_decision" in types_found, "Missing technical_decision"
        assert "pending_task" in types_found, "Missing pending_task"
        assert "unresolved_bug" in types_found, "Missing unresolved_bug"

        # -------------------------------------------------------------
        # 7. EVIDENCE TRACEABILITY WITH SOURCE REFERENCES
        # -------------------------------------------------------------
        print("\n[TEST 7/12] Evidence Traceability & Grounding Verification...")
        evidence_checked = 0
        for item in extracted_items:
            if item.get("evidence"):
                ev = item["evidence"]
                assert ev["document_id"] in [doc_pdf_id, doc_docx_id, doc_txt_id]
                assert ev["exact_quote"] is not None and len(ev["exact_quote"]) > 5
                assert "is_verified" in ev
                evidence_checked += 1
        print(f"  [OK] Verified {evidence_checked} evidence citations bound to source documents & pages")
        assert evidence_checked >= 1, "At least 1 evidence citation must be bound"

        # -------------------------------------------------------------
        # 8 & 9. KNOWLEDGE GAP DETECTOR & CONFLICT DETECTION
        # -------------------------------------------------------------
        print("\n[TEST 8-9/12] Knowledge Gap Detector & Conflicting Information...")
        gaps_res = await client.get(f"/api/knowledge/{project_id}/gaps", headers=admin_headers)
        assert gaps_res.status_code == 200
        gaps = gaps_res.json()
        gap_types = {g["gap_type"] for g in gaps}
        print(f"  [OK] Identified {len(gaps)} knowledge gaps:")
        for g in gaps:
            print(f"    - [{g['severity']}] {g['gap_type']}: {g['title']}")

        assert "missing_owner" in gap_types, "Failed to identify unassigned task"
        assert "unresolved_bug" in gap_types, "Failed to identify unresolved bug"
        assert "conflicting_deadline" in gap_types, "Failed to identify conflicting deadlines"

        # -------------------------------------------------------------
        # 10. HUMAN APPROVAL AND REJECTION WORKFLOW
        # -------------------------------------------------------------
        print("\n[TEST 10/12] Human Approval & Rejection Workflow...")
        item_to_approve = extracted_items[0]
        item_to_reject = extracted_items[1]

        # Approve item 1
        appr_res = await client.patch(f"/api/approvals/{item_to_approve['id']}", json={
            "action": "APPROVE",
            "review_comment": "Verified against production architecture spec",
            "edited_title": item_to_approve["title"] + " [Verified]"
        }, headers=admin_headers)
        assert appr_res.status_code == 200, f"Approve failed: {appr_res.text}"
        assert appr_res.json()["status"] == "APPROVED"
        assert "[Verified]" in appr_res.json()["title"]
        print("  [OK] Successfully approved item with reviewer comments and title edit")

        # Reject item 2
        rej_res = await client.patch(f"/api/approvals/{item_to_reject['id']}", json={
            "action": "REJECT",
            "review_comment": "Deprecated specification, reject from handover"
        }, headers=admin_headers)
        assert rej_res.status_code == 200, f"Reject failed: {rej_res.text}"
        assert rej_res.json()["status"] == "REJECTED"
        print("  [OK] Successfully rejected item with audit record")

        # -------------------------------------------------------------
        # 11. ROLE-BASED ACCESS CONTROL (RBAC)
        # -------------------------------------------------------------
        print("\n[TEST 11/12] Role-Based Access Control Scoping...")
        # Incoming member should only see approved items
        inc_k_res = await client.get(f"/api/knowledge/{project_id}", headers=incoming_headers)
        assert inc_k_res.status_code == 200
        incoming_items = inc_k_res.json()
        for itm in incoming_items:
            assert itm["status"] in ["APPROVED", "SUPPORTED"], f"Unauthorized status leaked to incoming member: {itm['status']}"
        print(f"  [OK] Incoming Member view strictly filtered ({len(incoming_items)} approved items visible)")

        # Incoming member attempting to delete project should receive 403 Forbidden
        del_res = await client.delete(f"/api/projects/{project_id}", headers=incoming_headers)
        assert del_res.status_code == 403, f"Expected 403 Forbidden, got {del_res.status_code}"
        print("  [OK] RBAC enforced: Incoming member denied destructive action (403 Forbidden)")

        # -------------------------------------------------------------
        # 12. HANDOVER PDF GENERATION (ReportLab)
        # -------------------------------------------------------------
        print("\n[TEST 12/12] Handover PDF Generation...")
        pdf_report_res = await client.get(f"/api/reports/{project_id}/download", headers=admin_headers)
        assert pdf_report_res.status_code == 200, f"Report download failed: {pdf_report_res.text}"
        assert pdf_report_res.headers["content-type"] == "application/pdf"
        assert pdf_report_res.content.startswith(b"%PDF-"), "Invalid PDF header signature"
        print(f"  [OK] Official PDF Handover report generated ({len(pdf_report_res.content)} bytes)")

        # -------------------------------------------------------------
        # 13. API ERROR HANDLING VERIFICATION
        # -------------------------------------------------------------
        print("\n[VERIFICATION] API Error Handling & Validation...")
        # Duplicate user registration
        dup_res = await client.post("/api/auth/register", json={
            "email": admin_email,
            "password": "anypassword",
            "full_name": "Duplicate User",
            "role": "Incoming Member"
        })
        assert dup_res.status_code == 400
        print("  [OK] Duplicate registration rejected (400 Bad Request)")

        # Bad password login
        bad_pw = await client.post("/api/auth/login", json={
            "email": admin_email,
            "password": "wrongpassword"
        })
        assert bad_pw.status_code == 401
        print("  [OK] Invalid password rejected (401 Unauthorized)")

        # Nonexistent project query
        not_found = await client.get("/api/projects/999999", headers=admin_headers)
        assert not_found.status_code == 404
        print("  [OK] Missing resource returns 404 Not Found")

        # -------------------------------------------------------------
        # 14. DATABASE PERSISTENCE VERIFICATION
        # -------------------------------------------------------------
        print("\n[VERIFICATION] Direct Database Persistence...")
        db = SessionLocal()
        try:
            persisted_proj = db.query(Project).filter(Project.id == project_id).first()
            assert persisted_proj is not None
            assert persisted_proj.name == "Audit Handover System Alpha"
            docs_count = db.query(Document).filter(Document.project_id == project_id).count()
            assert docs_count == 3
            print(f"  [OK] Database state validated: Project #{project_id} with {docs_count} documents persisted")
        finally:
            db.close()

    print("\n=================================================================")
    print(" ALL 12 AUDIT TESTS + VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(run_full_audit())
