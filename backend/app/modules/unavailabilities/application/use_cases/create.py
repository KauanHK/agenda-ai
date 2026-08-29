import uuid

from app.core.actors.user import UserActor
from app.modules.unavailabilities.application.authz import assert_can_write
from app.modules.unavailabilities.application.dtos.commands import (
    CreateUnavailabilityCommand,
)
from app.modules.unavailabilities.application.ports.unit_of_work import (
    UnavailabilitiesUnitOfWorkProtocol,
)
from app.modules.unavailabilities.domain.entities import (
    NewUnavailability,
    Unavailability,
)


class UnavailabilitiesCreator:
    def __init__(self, uow: UnavailabilitiesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def create(
        self,
        data: CreateUnavailabilityCommand,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> Unavailability:
        """Cria uma unavailability no estabelecimento especificado."""
        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            return await uow.unavailabilities.create(
                NewUnavailability(
                    establishment_id=establishment_id,
                    starts_at=data.starts_at,
                    ends_at=data.ends_at,
                    reason=data.reason,
                )
            )
