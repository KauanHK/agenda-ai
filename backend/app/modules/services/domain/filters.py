import uuid
from dataclasses import dataclass


@dataclass
class ServiceFilters:
    establishment_id: uuid.UUID
    q: str | None = None
    is_active: bool | None = None
