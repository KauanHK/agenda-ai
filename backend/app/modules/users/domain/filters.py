import uuid
from dataclasses import dataclass

from app.modules.users.domain.enums import UserRole


@dataclass
class UserFilters:
    q: str | None = None
    role: UserRole | None = None
    is_active: bool | None = True
    establishment_id: uuid.UUID | None = None
