import uuid

from app.core.actors.user import UserActor
from app.modules.operating_hours.application.authz import assert_can_write
from app.modules.operating_hours.application.dtos.commands import (
    ReplaceOperatingHoursCommand,
)
from app.modules.operating_hours.application.ports.unit_of_work import (
    OperatingHoursUnitOfWorkProtocol,
)
from app.modules.operating_hours.domain.entities import (
    NewOperatingHour,
    OperatingHour,
)


class OperatingHoursUpdater:
    def __init__(self, uow: OperatingHoursUnitOfWorkProtocol) -> None:
        """
        Inicializa um atualizador de horários de funcionamento.

        Args:
            uow (OperatingHoursUnitOfWorkProtocol):
                Unit of work de horários de funcionamento.
        """

        self._uow = uow

    async def update(
        self,
        data: ReplaceOperatingHoursCommand,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHour]:
        """
        Substitui todos os horários de funcionamento de um estabelecimento.

        Args:
            data (ReplaceOperatingHoursCommand):
                Nova lista completa de horários de funcionamento.
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                UUID do estabelecimento.
        """

        assert_can_write(actor, establishment_id)

        hours = [
            NewOperatingHour(
                establishment_id=establishment_id,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
            )
            for item in data.items
        ]

        async with self._uow as uow:
            return await uow.operating_hours.replace_all(establishment_id, hours)
