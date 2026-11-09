from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.documents import router as documents_router
from app.routers.knowledge import router as knowledge_router
from app.routers.approvals import router as approvals_router
from app.routers.reports import router as reports_router
from app.routers.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "projects_router",
    "documents_router",
    "knowledge_router",
    "approvals_router",
    "reports_router",
    "dashboard_router"
]
