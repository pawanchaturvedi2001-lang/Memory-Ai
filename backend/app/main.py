import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import (
    auth_router,
    projects_router,
    documents_router,
    knowledge_router,
    approvals_router,
    reports_router,
    dashboard_router
)
from app.services.demo_service import seed_demo_data

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Knowledge Handover & Team Continuity Platform"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Vite dev server on localhost:5173, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(knowledge_router, prefix=settings.API_V1_STR)
app.include_router(approvals_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def startup_event():
    """Seeds synthetic demo dataset on initial launch."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_demo_data(db)
    except Exception as e:
        print(f"Demo seeding notice: {e}")
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "documentation": "/docs"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "sqlite_connected",
        "version": settings.VERSION
    }


@app.post("/api/demo/seed")
def trigger_demo_seed(db: Session = Depends(get_db)):
    """Allows manual re-seeding of the synthetic demo dataset anytime."""
    proj = seed_demo_data(db)
    return {
        "message": "Synthetic demo dataset successfully seeded",
        "project_id": proj.id,
        "project_name": proj.name
    }
