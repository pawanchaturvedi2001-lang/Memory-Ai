import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import httpx
from app.main import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health
        res = await client.get("/api/health")
        print("Health check:", res.status_code, res.json())
        assert res.status_code == 200

        # 2. Login as Demo Admin
        res = await client.post("/api/auth/login", json={
            "email": "admin@memoryai.io",
            "password": "password123"
        })
        print("Login status:", res.status_code)
        assert res.status_code == 200
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get Projects
        res = await client.get("/api/projects", headers=headers)
        print("Projects status:", res.status_code, f"Found {len(res.json())} projects")
        assert res.status_code == 200
        proj_id = res.json()[0]["id"]

        # 4. Get Knowledge for project
        res = await client.get(f"/api/knowledge/{proj_id}", headers=headers)
        print("Knowledge status:", res.status_code, f"Found {len(res.json())} items")
        assert res.status_code == 200

        # 5. Get Gaps for project
        res = await client.get(f"/api/knowledge/{proj_id}/gaps", headers=headers)
        print("Gaps status:", res.status_code, f"Found {len(res.json())} gaps")
        assert res.status_code == 200

        # 6. Get Dashboard Stats
        res = await client.get("/api/dashboard/stats", headers=headers)
        print("Dashboard stats:", res.status_code, res.json())
        assert res.status_code == 200

        # 7. Generate PDF report
        res = await client.get(f"/api/reports/{proj_id}/download", headers=headers)
        print("PDF report status:", res.status_code, f"PDF size: {len(res.content)} bytes")
        assert res.status_code == 200
        assert len(res.content) > 1000

        print("\n ALL DIRECT ASYNC API TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_tests())
