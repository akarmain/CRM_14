import asyncio

from app.db.session import async_session_maker
from app.repositories.sqlalchemy.contacts_repo_impl import SqlAlchemyContactsRepository
from app.services.contact_service import ContactService


async def seed_contacts() -> None:
    async with async_session_maker() as session:
        repository = SqlAlchemyContactsRepository(session)
        service = ContactService(repository)
        await service.ensure_seed_contact()


if __name__ == "__main__":
    asyncio.run(seed_contacts())
