import uuid

from app.core.actors.user import UserActor
from app.modules.operating_hours.application.authz import assert_can_access
from app.modules.operating_hours.application.ports.unit_of_work import (
    OperatingHoursUnitOfWorkProtocol,
)
from app.modules.operating_hours.domain.entities import OperatingHour


class OperatingHoursReader:
    def __init__(self, uow: OperatingHoursUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de horários de funcionamento.

        Args:
            uow (OperatingHoursUnitOfWorkProtocol):
                Unit of work de horários de funcionamento.
        """

        self._uow = uow

    async def list(
        self,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHour]:
        """
        Lista os horários de funcionamento de um estabelecimento.

        Args:
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                UUID do estabelecimento.
        """

        assert_can_access(actor, establishment_id)

        async with self._uow as uow:
            return await uow.operating_hours.list_by_establishment(establishment_id)
