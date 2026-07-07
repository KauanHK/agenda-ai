import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.services.application._authz import assert_can_write
from app.modules.services.domain.model import Service
from app.modules.services.domain.schemas import ServiceRead
from app.modules.services.infra.repository import ServicesRepository


class ServicesActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(
        self,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceRead:
        """Ativa o serviço identificado por ``service_id``."""
        return await self._set_active_status(
            service_id=service_id,
            is_active=True,
            actor=actor,
            establishment_id=establishment_id,
        )

    async def deactivate(
        self,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceRead:
        """Desativa o serviço identificado por ``service_id``."""
        return await self._set_active_status(
            service_id=service_id,
            is_active=False,
            actor=actor,
            establishment_id=establishment_id,
        )

    async def _set_active_status(
        self,
        service_id: uuid.UUID,
        is_active: bool,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceRead:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ServicesRepository)
            service = await repo.get_by_id(service_id)
            self._assert_scope(service, establishment_id)

            service.is_active = is_active
            updated = await repo.update(service)
            return ServiceRead.model_validate(updated)

    def _assert_scope(self, service: Service, establishment_id: uuid.UUID) -> None:
        if service.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
