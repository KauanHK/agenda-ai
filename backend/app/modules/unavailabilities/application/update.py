import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.unavailabilities.application._authz import assert_can_write
from app.modules.unavailabilities.domain.model import Unavailability
from app.modules.unavailabilities.domain.schemas import (
    UnavailabilityRead,
    UnavailabilityUpdate,
)
from app.modules.unavailabilities.infra.repository import UnavailabilitiesRepository


class UnavailabilitiesUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        unavailability_id: uuid.UUID,
        data: UnavailabilityUpdate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> UnavailabilityRead:
        """Atualiza os campos da unavailability identificada por ``unavailability_id``."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(UnavailabilitiesRepository)
            unavailability = await repo.get_by_id(unavailability_id)
            self._assert_scope(unavailability, establishment_id)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(unavailability, field, value)

            updated = await repo.update(unavailability)
            return UnavailabilityRead.model_validate(updated)

    def _assert_scope(
        self, unavailability: Unavailability, establishment_id: uuid.UUID
    ) -> None:
        if unavailability.establishment_id != establishment_id:
            raise NotFoundError("Unavailability não encontrada.")
