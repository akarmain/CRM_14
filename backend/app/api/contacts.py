from fastapi import APIRouter, Depends

from app.schemas.contact import ContactRead
from app.services.contact_service import ContactService, get_contact_service

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    service: ContactService = Depends(get_contact_service),
) -> list[ContactRead]:
    contacts = await service.list_contacts()
    return [ContactRead.from_domain(contact) for contact in contacts]
