import uuid

from app.core.actors.user import UserActor
from app.core.pagination.params import Page, PageParams
from app.modules.clients.application.authz import assert_can_access
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.application.ports.unit_of_work import (
    ClientsUnitOfWorkProtocol,
)
from app.modules.clients.domain.entities import Client


class ClientsPaginator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: ClientFilters | None = None,
    ) -> Page[Client]:
        """Retorna uma página de clientes do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        filters = filters or ClientFilters()
        scoped_filters = ClientFilters(
            q=filters.q,
            is_active=filters.is_active,
            establishment_id=str(establishment_id),
        )

        async with self._uow as uow:
            return await uow.clients.paginate(
                page_params=page_params,
                filters=scoped_filters,
            )
