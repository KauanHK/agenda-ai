import uuid
from datetime import UTC, datetime

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.services.application._authz import assert_can_write
from app.modules.services.domain.model import Service
from app.modules.services.infra.repository import ServicesRepository


class ServicesDeleter:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def delete(
        self,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ServicesRepository)
            service = await repo.get_by_id(service_id)
            self._assert_scope(service, establishment_id)
            service.deleted_at = datetime.now(UTC)
            await repo.update(service)

    def _assert_scope(self, service: Service, establishment_id: uuid.UUID) -> None:
        if service.establishment_id != establishment_id:
            raise NotFoundError("Service not found.")
