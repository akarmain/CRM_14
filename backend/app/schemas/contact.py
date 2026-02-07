from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models.contact import Contact


class ContactBase(BaseModel):
    birth_date: date
    last_name: str
    first_name: str
    middle_name: str
    photo: str
    extra_fields: dict[str, Any] = Field(default_factory=dict)


class ContactRead(ContactBase):
    id: int

    @classmethod
    def from_domain(cls, contact: Contact) -> "ContactRead":
        if contact.id is None:
            raise ValueError("Contact id is required")
        return cls(
            id=contact.id,
            birth_date=contact.birth_date,
            last_name=contact.last_name,
            first_name=contact.first_name,
            middle_name=contact.middle_name,
            photo=contact.photo,
            extra_fields=contact.extra_fields,
        )
