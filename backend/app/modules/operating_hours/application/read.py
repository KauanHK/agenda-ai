import uuid

from app.core.actors.user import UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.operating_hours.application._authz import assert_can_access
from app.modules.operating_hours.domain.schemas import OperatingHourRead
from app.modules.operating_hours.infra.repository import OperatingHoursRepository


class OperatingHoursReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list(
        self,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHourRead]:
        assert_can_access(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(OperatingHoursRepository)
            hours = await repo.list_by_establishment(establishment_id)
            return [OperatingHourRead.model_validate(h) for h in hours]
