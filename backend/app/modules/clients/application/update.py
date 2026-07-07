import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.application._authz import assert_can_write
from app.modules.clients.domain.model import Client
from app.modules.clients.domain.schemas import ClientRead, ClientUpdate
from app.modules.clients.infra.repository import ClientsRepository


class ClientsUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        client_id: uuid.UUID,
        data: ClientUpdate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ClientRead:
        """Atualiza os campos do cliente identificado por ``client_id``."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ClientsRepository)
            client = await repo.get_by_id(client_id)
            self._assert_scope(client, establishment_id)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(client, field, value)

            try:
                updated = await repo.update(client)
            except IntegrityError as e:
                raise ConflictError(
                    "Telefone ou e-mail já cadastrado neste estabelecimento."
                ) from e

            return ClientRead.model_validate(updated)

    def _assert_scope(self, client: Client, establishment_id: uuid.UUID) -> None:
        if client.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
