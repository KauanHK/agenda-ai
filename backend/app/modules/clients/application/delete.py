import uuid
from datetime import UTC, datetime

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.application._authz import assert_can_write
from app.modules.clients.domain.model import Client
from app.modules.clients.infra.repository import ClientsRepository


class ClientsDeleter:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def delete(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ClientsRepository)
            client = await repo.get_by_id(client_id)
            self._assert_scope(client, establishment_id)
            client.deleted_at = datetime.now(UTC)
            await repo.update(client)

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Client not found.")
