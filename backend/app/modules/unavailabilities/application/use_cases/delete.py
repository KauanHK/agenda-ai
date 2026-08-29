import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.unavailabilities.application.authz import assert_can_write
from app.modules.unavailabilities.application.ports.unit_of_work import (
    UnavailabilitiesUnitOfWorkProtocol,
)
from app.modules.unavailabilities.domain.entities import Unavailability


class UnavailabilitiesDeleter:
    def __init__(self, uow: UnavailabilitiesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def delete(
        self,
        unavailability_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        """Remove permanentemente a unavailability identificada por `unavailability_id`."""
        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            unavailability = await uow.unavailabilities.get_by_id(unavailability_id)
            self._assert_scope(unavailability, establishment_id)
            await uow.unavailabilities.delete(unavailability_id)

    def _assert_scope(
        self, unavailability: Unavailability, establishment_id: uuid.UUID
    ) -> None:
        if unavailability.establishment_id != establishment_id:
            raise NotFoundError("Unavailability não encontrada.")
