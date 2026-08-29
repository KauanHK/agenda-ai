import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.clients.application.authz import assert_can_write
from app.modules.clients.application.ports.unit_of_work import (
    ClientsUnitOfWorkProtocol,
)
from app.modules.clients.domain.entities import Client, UpdateClient


class ClientsActivator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def activate(
        self,
        client_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> Client:
        """Ativa o cliente identificado por `client_id`."""
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
    ) -> Client:
        """Desativa o cliente identificado por `client_id`."""
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
    ) -> Client:
        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            client = await uow.clients.get_by_id(client_id)
            self._assert_scope(client, establishment_id)

            return await uow.clients.update(
                id_=client_id,
                update_command=UpdateClient(is_active=is_active),
            )

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
