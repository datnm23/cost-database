from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    projects,
    files,
    line_items,
    sec_codes,
    analytics,
    users,
    master_items,
    naming_validation,
    price_history,
    versions,
    matcher,
    synonyms,
    pending_items,
    quarantine,
    units,
    templates,
    project_work_items,
    training_logs,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(files.router, prefix="/files", tags=["BOQ Files"])
api_router.include_router(line_items.router, prefix="/line-items", tags=["Line Items"])
api_router.include_router(sec_codes.router, prefix="/sec-codes", tags=["SEC Codes"])
api_router.include_router(master_items.router, prefix="/master-items", tags=["Master Items"])
api_router.include_router(price_history.router, prefix="/master-items", tags=["Price History"])
api_router.include_router(versions.router, prefix="/projects", tags=["Version Comparison"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(naming_validation.router, tags=["Naming Validation"])
api_router.include_router(matcher.router, prefix="/matcher", tags=["Matcher Management"])
api_router.include_router(synonyms.router, tags=["Synonyms"])
api_router.include_router(pending_items.router, prefix="/pending-items", tags=["Pending Items"])
api_router.include_router(quarantine.router, prefix="/quarantine", tags=["Quarantine"])
api_router.include_router(units.router, tags=["Unit Standards"])
api_router.include_router(templates.router, prefix="/templates", tags=["Column Mapping Templates"])
api_router.include_router(project_work_items.router, prefix="/project-work-items", tags=["Project Work Items"])
api_router.include_router(training_logs.router, prefix="/training-logs", tags=["Training Logs"])
