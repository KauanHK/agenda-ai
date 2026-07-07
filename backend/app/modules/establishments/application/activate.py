import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.db.unit_of_work import UnitOfWork
from app.modules.establishments.domain.schemas import EstablishmentRead
from app.modules.establishments.infra.repository import EstablishmentsRepository


class EstablishmentsActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(
        self,
        id: uuid.UUID,
    ) -> EstablishmentRead:
        """
        Ativa um estabelecimento existente.

        Args:
            id (uuid.UUID): O ID do estabelecimento a ser ativado.

        Returns:
            EstablishmentRead: O estabelecimento ativado.
        """

        return await self._set_active_status(
            id=id,
            is_active=True,
        )

    async def deactivate(
        self,
        id: uuid.UUID,
    ) -> EstablishmentRead:
        """
        Desativa um estabelecimento existente.

        Args:
            id (uuid.UUID): O ID do estabelecimento a ser desativado.

        Returns:
            EstablishmentRead: O estabelecimento desativado.
        """

        return await self._set_active_status(
            id=id,
            is_active=False,
        )

    async def _set_active_status(
        self,
        id: uuid.UUID,
        is_active: bool,
    ) -> EstablishmentRead:
        """
        Define o status de ativo de um estabelecimento existente.

        Args:
            id (uuid.UUID): O ID do estabelecimento a ser atualizado.
            is_active (bool): O novo status de ativo.

        Returns:
            EstablishmentRead: O estabelecimento atualizado.
        """

        async with self._uow:
            repo = self._uow.repository(EstablishmentsRepository)
            establishment = await repo.get_by_id(id)
            establishment.is_active = is_active
            if not is_active:
                establishment.deleted_at = datetime.now(
                    tz=ZoneInfo(establishment.timezone)
                )
            establishment = await repo.update(establishment)
            return EstablishmentRead.model_validate(establishment)
