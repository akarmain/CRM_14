from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.interface.api.v1.routes_audit import router as audit_router
from app.interface.api.v1.routes_health import router as health_router
from app.interface.api.v1.routes_leads import router as leads_router
from app.interface.api.v1.routes_reports import router as reports_router
from app.interface.api.v1.routes_return_requests import router as return_requests_router
from app.interface.api.v1.routes_session import router as session_router


def configure_cors(application):
    # Учебный MVP: CORS намеренно открыт для любого origin, чтобы упростить
    # запуск демо (frontend на любом хосте/порту + cookie-сессия). В продакшене
    # здесь следует ограничить список origin значением settings.cors_allowed_origins.
    return CORSMiddleware(
        application,
        allow_origins=[],
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    application = FastAPI(title="mini_crm_simple", version="0.1.0")
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="mini_crm_session",
        same_site="lax",
        https_only=settings.session_https_only,
    )
    register_exception_handlers(application)

    application.include_router(health_router, prefix="/api/v1", tags=["health"])
    application.include_router(session_router, prefix="/api/v1", tags=["session"])
    application.include_router(leads_router, prefix="/api/v1", tags=["leads"])
    application.include_router(return_requests_router, prefix="/api/v1", tags=["return-requests"])
    application.include_router(reports_router, prefix="/api/v1", tags=["reports"])
    application.include_router(audit_router, prefix="/api/v1", tags=["audit"])

    return application


app = configure_cors(create_app())
