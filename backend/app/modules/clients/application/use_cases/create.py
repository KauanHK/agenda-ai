import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.modules.clients.application.authz import assert_can_write
from app.modules.clients.application.dtos.commands import CreateClientCommand
from app.modules.clients.application.ports.unit_of_work import (
    ClientsUnitOfWorkProtocol,
)
from app.modules.clients.domain.entities import Client, NewClient


class ClientsCreator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def create(
        self,
        data: CreateClientCommand,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> Client:
        """Cria um cliente no estabelecimento especificado."""
        assert_can_write(actor, establishment_id)

        new_client = NewClient(
            establishment_id=establishment_id,
            name=data.name,
            phone=data.phone,
            email=data.email,
        )

        async with self._uow as uow:
            try:
                return await uow.clients.create(create_command=new_client)
            except IntegrityError as e:
                raise ConflictError(
                    "Telefone ou e-mail já cadastrado neste estabelecimento."
                ) from e
