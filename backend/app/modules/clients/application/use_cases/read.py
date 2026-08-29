import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.clients.application.authz import assert_can_access
from app.modules.clients.application.ports.unit_of_work import (
    ClientsUnitOfWorkProtocol,
)
from app.modules.clients.domain.entities import Client


class ClientsReader:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> Client:
        """Retorna o cliente do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        async with self._uow as uow:
            client = await uow.clients.get_by_id(client_id)
            self._assert_scope(client, establishment_id)
            return client

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
