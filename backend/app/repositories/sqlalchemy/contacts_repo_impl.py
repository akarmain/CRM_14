from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContactModel
from app.domain.models.contact import Contact


class SqlAlchemyContactsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_contacts(self) -> list[Contact]:
        result = await self._session.execute(
            select(ContactModel).order_by(ContactModel.last_name, ContactModel.first_name)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def add_contact(self, contact: Contact) -> Contact:
        model = ContactModel(
            birth_date=contact.birth_date,
            last_name=contact.last_name,
            first_name=contact.first_name,
            middle_name=contact.middle_name,
            photo=contact.photo,
            extra_fields=contact.extra_fields,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: ContactModel) -> Contact:
        return Contact(
            id=model.id,
            birth_date=model.birth_date,
            last_name=model.last_name,
            first_name=model.first_name,
            middle_name=model.middle_name,
            photo=model.photo,
            extra_fields=model.extra_fields or {},
        )
