import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.application._authz import assert_can_access
from app.modules.clients.domain.filters import ClientFilters
from app.modules.clients.domain.model import Client
from app.modules.clients.domain.schemas import ClientRead
from app.modules.clients.infra.repository import ClientsRepository


class ClientsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ClientRead:
        """Retorna o cliente do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ClientsRepository)
            client = await repo.get_by_id(client_id)
            self._assert_scope(client, establishment_id)
            return ClientRead.model_validate(client)

    async def paginate(
        self,
        pagination: PaginationParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: ClientFilters | None = None,
    ) -> PaginatedResponse[ClientRead]:
        """Retorna uma página de clientes do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        filters = filters or ClientFilters()

        async with self._uow:
            repo = self._uow.repository(ClientsRepository)

            scoped_filters = ClientFilters(
                q=filters.q,
                is_active=filters.is_active,
                establishment_id=str(establishment_id),
            )

            clients = await repo.list(pagination=pagination, filters=scoped_filters)
            total = await repo.count(filters=scoped_filters)

            return build_paginated_response(
                items=[ClientRead.model_validate(c) for c in clients],
                total=total,
                params=pagination,
            )

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
