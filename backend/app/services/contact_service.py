from datetime import date

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.models.contact import Contact
from app.repositories.contacts_repo import ContactsRepository
from app.repositories.sqlalchemy.contacts_repo_impl import SqlAlchemyContactsRepository


class ContactService:
    def __init__(self, repository: ContactsRepository) -> None:
        self._repository = repository

    async def list_contacts(self) -> list[Contact]:
        return await self._repository.list_contacts()

    async def ensure_seed_contact(self) -> None:
        existing = await self._repository.list_contacts()
        if existing:
            return
        sample = Contact(
            birth_date=date(1990, 5, 12),
            last_name="Ivanov",
            first_name="Ivan",
            middle_name="Ivanovich",
            photo="https://example.com/contacts/ivanov.jpg",
            extra_fields={"telegram": "@ivanov"},
        )
        await self._repository.add_contact(sample)


def get_contact_service(
    session: AsyncSession = Depends(get_session),
) -> ContactService:
    repository = SqlAlchemyContactsRepository(session)
    return ContactService(repository)
