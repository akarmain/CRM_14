from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.interface.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", mode=settings.storage_mode)
