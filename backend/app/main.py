from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.interface.api.v1.routes_health import router as health_router
from app.interface.api.v1.routes_leads import router as leads_router


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    application = FastAPI(title="mini_crm_simple", version="0.1.0")
    register_exception_handlers(application)

    application.include_router(health_router, prefix="/api/v1", tags=["health"])
    application.include_router(leads_router, prefix="/api/v1", tags=["leads"])

    return application


app = create_app()
