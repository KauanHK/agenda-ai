import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.db.unit_of_work import UnitOfWork
from app.modules.clients.application._authz import assert_can_write
from app.modules.clients.domain.model import Client
from app.modules.clients.domain.schemas import ClientCreate, ClientRead
from app.modules.clients.infra.repository import ClientsRepository


class ClientsCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        data: ClientCreate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ClientRead:
        """Cria um cliente no estabelecimento especificado."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ClientsRepository)

            client = Client(
                establishment_id=establishment_id,
                name=data.name,
                phone=data.phone,
                email=data.email,
            )

            try:
                client = await repo.create(client)
            except IntegrityError as e:
                raise ConflictError(
                    "Telefone ou e-mail já cadastrado neste estabelecimento."
                ) from e

            return ClientRead.model_validate(client)
