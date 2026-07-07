import uuid

from app.core.actors.user import UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.operating_hours.application._authz import assert_can_write
from app.modules.operating_hours.domain.model import OperatingHour
from app.modules.operating_hours.domain.schemas import (
    OperatingHourRead,
    OperatingHoursUpdate,
)
from app.modules.operating_hours.infra.repository import OperatingHoursRepository


class OperatingHoursUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        data: OperatingHoursUpdate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHourRead]:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(OperatingHoursRepository)
            hours = [
                OperatingHour(
                    establishment_id=establishment_id,
                    weekday=item.weekday,
                    start_time=item.start_time,
                    end_time=item.end_time,
                )
                for item in data.items
            ]
            hours = await repo.replace_all(establishment_id, hours)
            return [OperatingHourRead.model_validate(h) for h in hours]
