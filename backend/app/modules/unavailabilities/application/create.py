import uuid

from app.core.actors.user import UserActor
from app.db.unit_of_work import UnitOfWork
from app.modules.unavailabilities.application._authz import assert_can_write
from app.modules.unavailabilities.domain.model import Unavailability
from app.modules.unavailabilities.domain.schemas import (
    UnavailabilityCreate,
    UnavailabilityRead,
)
from app.modules.unavailabilities.infra.repository import UnavailabilitiesRepository


class UnavailabilitiesCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        data: UnavailabilityCreate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> UnavailabilityRead:
        """Cria uma unavailability no estabelecimento especificado."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(UnavailabilitiesRepository)

            unavailability = Unavailability(
                establishment_id=establishment_id,
                starts_at=data.starts_at,
                ends_at=data.ends_at,
                reason=data.reason,
            )

            unavailability = await repo.create(unavailability)
            return UnavailabilityRead.model_validate(unavailability)
