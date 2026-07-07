import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.services.application._authz import assert_can_write
from app.modules.services.domain.model import Service
from app.modules.services.domain.schemas import ServiceRead, ServiceUpdate
from app.modules.services.infra.repository import ServicesRepository


class ServicesUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        service_id: uuid.UUID,
        data: ServiceUpdate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceRead:
        """Atualiza os campos do serviço identificado por ``service_id``."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ServicesRepository)
            service = await repo.get_by_id(service_id)
            self._assert_scope(service, establishment_id)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(service, field, value)

            try:
                updated = await repo.update(service)
            except IntegrityError as e:
                raise ConflictError(
                    "Já existe um serviço com este nome neste estabelecimento."
                ) from e

            return ServiceRead.model_validate(updated)

    def _assert_scope(self, service: Service, establishment_id: uuid.UUID) -> None:
        if service.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
