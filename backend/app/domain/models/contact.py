from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(slots=True)
class Contact:
    birth_date: date
    last_name: str
    first_name: str
    middle_name: str
    photo: str
    extra_fields: dict[str, Any] = field(default_factory=dict)
    id: int | None = None
