# PROJECT MEMORY AI
### Intelligent Knowledge Handover & Team Continuity Platform

> **Hackathon MVP Development**  
> An autonomous, evidence-grounded AI platform that prevents critical project knowledge, architectural decisions, and context from being lost when employees or developers leave a team.

---

## 1. Executive Summary & Problem Solved

Software engineering teams lose up to **42% of institutional knowledge** when a key engineer or architect departs. Handover documentation is typically fragmented across unstructured Slack threads, obsolete READMEs, and meeting notes, leading to:
- **Abandoned tasks without owners**
- **Conflicting timelines and architectural drift**
- **Silent, unresolved production bugs**
- **Unverified decisions without documentation or ADRs**
- **External dependencies lacking configuration credentials**

**Project Memory AI** solves this by ingesting project documentation (PDF, DOCX, TXT), extracting structured knowledge items, deterministically detecting knowledge gaps and inconsistencies, verifying every claim against verbatim source excerpts, enforcing human sign-off governance, and generating enterprise PDF handover reports for incoming engineers.

---

## 2. Technology Stack

### Frontend
- **Framework:** React 19 + Vite 8
- **Language:** JavaScript (ESNext)
- **Styling:** Tailwind CSS v4 (Clean white enterprise theme with deep blue accents)
- **Routing:** React Router DOM v7
- **HTTP Client:** Axios (with automatic JWT authentication interceptors)
- **Iconography:** Lucide React

### Backend
- **Framework:** Python 3.14 + FastAPI
- **ORM & DB:** SQLAlchemy 2.0 + SQLite (PostgreSQL architecture compatible)
- **Data Validation:** Pydantic v2
- **Database Migrations:** Alembic
- **Authentication:** JWT (JSON Web Tokens) with PBKDF2/bcrypt hashing & RBAC
- **Document Processing:** PyMuPDF & PyPDFium2 (PDF), python-docx (DOCX), Python file processing (TXT)
- **Report Generation:** ReportLab Platypus PDF Engine
- **Test Suite:** Pytest

---

## 3. Platform Modules & Features

| Module | Purpose | Status |
| :--- | :--- | :--- |
| **Module 1: Authentication & RBAC** | User registration, login, JWT issuance, and 4 role tiers (`Admin`, `Manager`, `Outgoing Member`, `Incoming Member`). | ✅ Operational |
| **Module 2: Document Ingestion** | Drag-and-drop upload supporting PDF, DOCX, TXT (up to 30MB) with extraction status and text normalization. | ✅ Operational |
| **Module 3: AI Knowledge Extraction** | Extracts 9 categories: technical decisions, pending tasks, unresolved bugs, risks, dependencies, ownership, context, tech stack, architecture. | ✅ Operational |
| **Module 4: Evidence Traceability** | Binds every claim to an exact quote, document ID, page number, and calculates exact/partial verification match confidence. | ✅ Operational |
| **Module 5: Knowledge Gap Detector** | **Main Innovation:** Deterministic Python rule engine identifying unassigned tasks, conflicting deadlines, unverified claims, and active bugs. | ✅ Operational |
| **Module 6: Human Review & Approval** | Human-in-the-loop governance. Outgoing leads approve, edit, or reject items; incoming members only see verified handover items. | ✅ Operational |
| **Module 7: Handover Report** | ReportLab PDF engine compiling all 10 required project sections into a formatted downloadable PDF document. | ✅ Operational |

---

## 4. Synthetic Demo Dataset: ApexCommerce Platform

The platform includes a built-in synthetic dataset designed specifically for hackathon judging:
**`ApexCommerce - NextGen Enterprise E-Commerce Platform`**

It intentionally embeds 5 real-world anomalies that Project Memory AI autonomously identifies:
1. **Unassigned Task:** `"Optimize Redis cart session TTL"` has `owner: null`.
2. **Conflicting Deadlines:** `"Checkout Service Performance Optimization"` has conflicting deadlines: `2026-11-15` vs `2026-12-05`.
3. **Unresolved Bug:** `"BUG-1082: Checkout 500 Error on Zero-Decimal Currencies (JPY, KRW)"` flagged as active critical defect.
4. **Missing Dependency:** `"ShipStation Logistics API"` unconfigured without credentials.
5. **Unverified Decision:** `"Adoption of ZeroMQ for Distributed IPC"` lacks supporting documentation or ADR.

---

## 5. Quick Demo Credentials

For quick evaluation during demonstrations, use the pre-configured accounts:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@memoryai.io` | `password123` | Full access to all projects, user management, and system settings. |
| **Manager** | `manager@memoryai.io` | `password123` | Project management, approvals, and report exports. |
| **Outgoing Lead** | `outgoing@memoryai.io` | `password123` | Ingests documents, edits claims, resolves gaps, signs off items. |
| **Incoming Dev** | `incoming@memoryai.io` | `password123` | Reads approved handover items, assigned onboarding tasks, and reports. |

*Tip: You can also use the role quick-switcher in the top navbar to switch roles instantly.*

---

## 6. How to Run Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ (Tested on Node.js 24)

### 1. Start the Backend API (FastAPI)
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Start the Frontend (React + Vite)
```bash
cd frontend
npm run dev
```
- Application Dashboard: `http://localhost:5173`

---

## 7. Running Backend Tests

Run the complete integration and regression test suite:
```bash
cd backend
python -m pytest tests/test_backend.py -v
```
Verifies:
- User registration and login
- Project creation and retrieval
- Document upload and text extraction
- AI knowledge synthesis
- Knowledge gap detection rules
- Approval governance workflow
- ReportLab PDF generation
- Dashboard statistics calculation

---

## 8. Cloud Deployment (1-Click Launch)

Project Memory AI is pre-configured for cloud deployment on **Render** (FastAPI Backend) and **Vercel** (React Frontend).

### Step 1: Deploy Backend to Render (1-Click)
Deploy the FastAPI backend and auto-run database migrations:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/pawanchaturvedi2001-lang/Memory-Ai)

- **Blueprint File:** Root `render.yaml` handles build, database setup, and Uvicorn server startup automatically.
- Once deployed, copy your Render service URL (e.g., `https://project-memory-ai-backend.onrender.com`).
- Verify API Health: `https://<YOUR-RENDER-BACKEND>/api/health` -> `{"status": "healthy"}`
- Interactive Swagger UI: `https://<YOUR-RENDER-BACKEND>/docs`

### Step 2: Deploy Frontend to Vercel (1-Click)
Deploy the React 19 + Vite dashboard:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/pawanchaturvedi2001-lang/Memory-Ai&root-directory=frontend&env=VITE_API_URL&envDescription=Backend%20API%20Base%20URL%20from%20Render)

- **Root Directory:** `frontend`
- **Framework Preset:** Vite
- **Environment Variable:** Set `VITE_API_URL` to your Render backend URL (e.g. `https://project-memory-ai-backend.onrender.com`).

