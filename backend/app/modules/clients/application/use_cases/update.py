import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.clients.application.authz import assert_can_write
from app.modules.clients.application.dtos.commands import UpdateClientCommand
from app.modules.clients.application.ports.unit_of_work import (
    ClientsUnitOfWorkProtocol,
)
from app.modules.clients.domain.entities import Client, UpdateClient


class ClientsUpdater:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def update(
        self,
        client_id: uuid.UUID,
        data: UpdateClientCommand,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> Client:
        """
        Atualiza os campos do cliente identificado por `client_id`.

        Raises:
            NotFoundError:
                Se o cliente não existir ou pertencer a outro estabelecimento.
            ConflictError:
                Se o telefone ou e-mail já estiver em uso no estabelecimento.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            client = await uow.clients.get_by_id(client_id)
            self._assert_scope(client, establishment_id)

            try:
                return await uow.clients.update(
                    id_=client_id,
                    update_command=UpdateClient(**data.defined_values()),
                )
            except IntegrityError as e:
                raise ConflictError(
                    "Telefone ou e-mail já cadastrado neste estabelecimento."
                ) from e

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
