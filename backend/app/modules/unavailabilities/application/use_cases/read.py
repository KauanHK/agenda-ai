import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination.params import Page, PageParams
from app.modules.unavailabilities.application.authz import assert_can_access
from app.modules.unavailabilities.application.dtos.filters import (
    UnavailabilityFilters,
)
from app.modules.unavailabilities.application.ports.unit_of_work import (
    UnavailabilitiesUnitOfWorkProtocol,
)
from app.modules.unavailabilities.domain.entities import Unavailability


class UnavailabilitiesReader:
    def __init__(self, uow: UnavailabilitiesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        unavailability_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> Unavailability:
        """Retorna a unavailability do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        async with self._uow as uow:
            unavailability = await uow.unavailabilities.get_by_id(unavailability_id)
            self._assert_scope(unavailability, establishment_id)
            return unavailability

    async def paginate(
        self,
        page_params: PageParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: UnavailabilityFilters | None = None,
    ) -> Page[Unavailability]:
        """Retorna uma página de unavailabilities do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        filters = filters or UnavailabilityFilters()
        scoped_filters = UnavailabilityFilters(
            establishment_id=establishment_id,
            starts_at_from=filters.starts_at_from,
            starts_at_to=filters.starts_at_to,
        )

        async with self._uow as uow:
            return await uow.unavailabilities.paginate(
                page_params=page_params,
                filters=scoped_filters,
            )

    def _assert_scope(
        self, unavailability: Unavailability, establishment_id: uuid.UUID
    ) -> None:
        if unavailability.establishment_id != establishment_id:
            raise NotFoundError("Unavailability não encontrada.")
