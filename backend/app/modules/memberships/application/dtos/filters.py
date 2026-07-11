import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MembershipFilters:
    """Filtros de busca/paginação de memberships."""

    establishment_id: uuid.UUID | None = None
