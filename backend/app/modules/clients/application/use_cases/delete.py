import uuid
from datetime import UTC, datetime

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.clients.application.authz import assert_can_write
from app.modules.clients.application.ports.unit_of_work import (
    ClientsUnitOfWorkProtocol,
)
from app.modules.clients.domain.entities import Client, UpdateClient


class ClientsDeleter:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def delete(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        """
        Remove (soft-delete) o cliente identificado por `client_id`, marcando
        `deleted_at`.

        Raises:
            NotFoundError:
                Se o cliente não existir ou pertencer a outro estabelecimento.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            client = await uow.clients.get_by_id(client_id)
            self._assert_scope(client, establishment_id)
            await uow.clients.update(
                id_=client_id,
                update_command=UpdateClient(deleted_at=datetime.now(UTC)),
            )

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Client not found.")
