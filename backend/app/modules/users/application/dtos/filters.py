import uuid
from dataclasses import dataclass

from app.core.roles import UserRole


@dataclass(frozen=True, slots=True)
class UserFilters:
    """Filtros de busca/paginação de usuários."""

    q: str | None = None
    role: UserRole | None = None
    is_active: bool | None = True
    establishment_id: uuid.UUID | None = None
