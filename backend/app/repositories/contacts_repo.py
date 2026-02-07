from typing import Protocol

from app.domain.models.contact import Contact


class ContactsRepository(Protocol):
    async def list_contacts(self) -> list[Contact]:
        ...

    async def add_contact(self, contact: Contact) -> Contact:
        ...
