from datetime import date
from typing import Any

from sqlalchemy import Date, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContactModel(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(120), nullable=False)
    photo: Mapped[str] = mapped_column(String(512), nullable=False)
    extra_fields: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
