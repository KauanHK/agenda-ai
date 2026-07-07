import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.db.unit_of_work import UnitOfWork
from app.modules.services.application._authz import assert_can_write
from app.modules.services.domain.model import Service
from app.modules.services.domain.schemas import ServiceCreate, ServiceRead
from app.modules.services.infra.repository import ServicesRepository


class ServicesCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        data: ServiceCreate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceRead:
        """Cria um serviço no estabelecimento especificado."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ServicesRepository)

            service = Service(
                establishment_id=establishment_id,
                name=data.name,
                description=data.description,
                duration_minutes=data.duration_minutes,
                price=data.price,
            )

            try:
                service = await repo.create(service)
            except IntegrityError as e:
                raise ConflictError(
                    "Já existe um serviço com este nome neste estabelecimento."
                ) from e

            return ServiceRead.model_validate(service)
