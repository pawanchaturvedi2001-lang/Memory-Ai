import os
import sys
import pytest
import asyncio
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app


def test_complete_backend_workflow():
    async def async_runner():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Health check
            res = await client.get("/api/health")
            assert res.status_code == 200
            assert res.json()["status"] == "healthy"

            # 2. Register a new user
            reg_res = await client.post("/api/auth/register", json={
                "email": "testdev@memoryai.io",
                "password": "strongpassword123",
                "full_name": "Test Engineer",
                "role": "Manager"
            })
            assert reg_res.status_code == 201
            token = reg_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 3. Create a project
            proj_res = await client.post("/api/projects", json={
                "name": "Integration Test Platform",
                "description": "Automated test suite project"
            }, headers=headers)
            assert proj_res.status_code == 201
            proj_id = proj_res.json()["id"]

            # 4. Upload a document
            doc_content = (
                "## Project Decisions\n"
                "- Decision: Adopted FastAPI for backend API.\n\n"
                "## Tasks\n"
                "- Implement OAuth login: Owner: null. Deadline: 2026-12-01. Priority: HIGH.\n"
                "- Setup Postgres replica: Assigned to Alex. Deadline: null. Priority: MEDIUM.\n\n"
                "## Known Bugs\n"
                "- Unresolved defect: Memory leak in session worker. Status: UNRESOLVED.\n"
            )
            files = {"file": ("integration_notes.txt", doc_content.encode("utf-8"), "text/plain")}
            data = {"project_id": str(proj_id), "auto_extract": "true"}

            up_res = await client.post("/api/documents/upload", data=data, files=files, headers=headers)
            assert up_res.status_code == 201
            assert up_res.json()["processing_status"] == "PROCESSED"

            # 5. Verify knowledge extracted
            k_res = await client.get(f"/api/knowledge/{proj_id}", headers=headers)
            assert k_res.status_code == 200
            items = k_res.json()
            assert len(items) >= 2

            # 6. Verify knowledge gap detection
            gaps_res = await client.get(f"/api/knowledge/{proj_id}/gaps", headers=headers)
            assert gaps_res.status_code == 200
            gaps = gaps_res.json()
            assert len(gaps) >= 1

            # 7. Review and Approve an item
            target_item = items[0]
            appr_res = await client.patch(f"/api/approvals/{target_item['id']}", json={
                "action": "APPROVE",
                "review_comment": "Verified and signed off by lead engineer"
            }, headers=headers)
            assert appr_res.status_code == 200
            assert appr_res.json()["status"] == "APPROVED"

            # 8. Handover Report PDF Download
            pdf_res = await client.get(f"/api/reports/{proj_id}/download", headers=headers)
            assert pdf_res.status_code == 200
            assert pdf_res.headers["content-type"] == "application/pdf"
            assert len(pdf_res.content) > 1000

            # 9. Dashboard statistics
            stats_res = await client.get("/api/dashboard/stats", headers=headers)
            assert stats_res.status_code == 200
            assert stats_res.json()["total_projects"] >= 1

    asyncio.run(async_runner())
