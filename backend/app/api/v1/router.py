from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    projects,
    files,
    line_items,
    sec_codes,
    analytics,
    users
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(files.router, prefix="/files", tags=["BOQ Files"])
api_router.include_router(line_items.router, prefix="/line-items", tags=["Line Items"])
api_router.include_router(sec_codes.router, prefix="/sec-codes", tags=["SEC Codes"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
