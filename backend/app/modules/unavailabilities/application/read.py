import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.unavailabilities.application._authz import assert_can_access
from app.modules.unavailabilities.domain.filters import UnavailabilityFilters
from app.modules.unavailabilities.domain.model import Unavailability
from app.modules.unavailabilities.domain.schemas import UnavailabilityRead
from app.modules.unavailabilities.infra.repository import UnavailabilitiesRepository


class UnavailabilitiesReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        unavailability_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> UnavailabilityRead:
        """Retorna a unavailability do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(UnavailabilitiesRepository)
            unavailability = await repo.get_by_id(unavailability_id)
            self._assert_scope(unavailability, establishment_id)
            return UnavailabilityRead.model_validate(unavailability)

    async def paginate(
        self,
        pagination: PaginationParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: UnavailabilityFilters | None = None,
    ) -> PaginatedResponse[UnavailabilityRead]:
        """Retorna uma página de unavailabilities do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        filters = filters or UnavailabilityFilters()

        async with self._uow:
            repo = self._uow.repository(UnavailabilitiesRepository)

            scoped_filters = UnavailabilityFilters(
                starts_at_from=filters.starts_at_from,
                starts_at_to=filters.starts_at_to,
                establishment_id=str(establishment_id),
            )

            items = await repo.list(pagination=pagination, filters=scoped_filters)
            total = await repo.count(filters=scoped_filters)

            return build_paginated_response(
                items=[UnavailabilityRead.model_validate(u) for u in items],
                total=total,
                params=pagination,
            )

    def _assert_scope(
        self, unavailability: Unavailability, establishment_id: uuid.UUID
    ) -> None:
        if unavailability.establishment_id != establishment_id:
            raise NotFoundError("Unavailability não encontrada.")
