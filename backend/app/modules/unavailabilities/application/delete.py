import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.unavailabilities.application._authz import assert_can_write
from app.modules.unavailabilities.domain.model import Unavailability
from app.modules.unavailabilities.infra.repository import UnavailabilitiesRepository


class UnavailabilitiesDeleter:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def delete(
        self,
        unavailability_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        """Remove permanentemente a unavailability identificada por ``unavailability_id``."""
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(UnavailabilitiesRepository)
            unavailability = await repo.get_by_id(unavailability_id)
            self._assert_scope(unavailability, establishment_id)
            await repo.delete(unavailability)

    def _assert_scope(
        self, unavailability: Unavailability, establishment_id: uuid.UUID
    ) -> None:
        if unavailability.establishment_id != establishment_id:
            raise NotFoundError("Unavailability não encontrada.")
