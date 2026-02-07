from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import contacts
from app.core.config import settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.cors_origins_list, # Опасный момент 
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origins=["*"],
    )

    app.include_router(contacts.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
