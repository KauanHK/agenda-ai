import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.application._authz import assert_can_write
from app.modules.clients.domain.model import Client
from app.modules.clients.domain.schemas import ClientRead
from app.modules.clients.infra.repository import ClientsRepository


class ClientsActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ClientRead:
        """Ativa o cliente identificado por ``client_id``."""
        return await self._set_active_status(
            client_id=client_id,
            is_active=True,
            actor=actor,
            establishment_id=establishment_id,
        )

    async def deactivate(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ClientRead:
        """Desativa o cliente identificado por ``client_id``."""
        return await self._set_active_status(
            client_id=client_id,
            is_active=False,
            actor=actor,
            establishment_id=establishment_id,
        )

    async def _set_active_status(
        self,
        client_id: uuid.UUID,
        is_active: bool,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ClientRead:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ClientsRepository)
            client = await repo.get_by_id(client_id)
            self._assert_scope(client, establishment_id)

            client.is_active = is_active
            updated = await repo.update(client)
            return ClientRead.model_validate(updated)

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
