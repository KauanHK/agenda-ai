import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.types import UNSET, Unset
from app.modules.establishments.application.ports.unit_of_work import (
    EstablishmentsUnitOfWorkProtocol,
)
from app.modules.establishments.domain.entities import (
    Establishment,
    UpdateEstablishment,
)


class EstablishmentsActivator:
    def __init__(self, uow: EstablishmentsUnitOfWorkProtocol) -> None:
        """
        Inicializa um ativador de estabelecimentos.

        Args:
            uow (EstablishmentsUnitOfWorkProtocol):
                Unit of work de estabelecimentos.
        """

        self._uow = uow

    async def activate(self, id_: uuid.UUID) -> Establishment:
        """
        Ativa um estabelecimento existente.

        Args:
            id_ (uuid.UUID): O ID do estabelecimento a ser ativado.
        """

        return await self._set_active_status(id_=id_, is_active=True)

    async def deactivate(self, id_: uuid.UUID) -> Establishment:
        """
        Desativa um estabelecimento existente.

        Args:
            id_ (uuid.UUID): O ID do estabelecimento a ser desativado.
        """

        return await self._set_active_status(id_=id_, is_active=False)

    async def _set_active_status(
        self,
        id_: uuid.UUID,
        is_active: bool,
    ) -> Establishment:
        """
        Define o status de ativo de um estabelecimento existente.

        Ao desativar, registra `deleted_at` no fuso horário do próprio
        estabelecimento.
        """

        async with self._uow as uow:
            deleted_at: datetime | Unset = UNSET
            if not is_active:
                establishment = await uow.establishments.get_by_id(id_)
                deleted_at = datetime.now(tz=ZoneInfo(establishment.timezone))

            return await uow.establishments.update(
                id_=id_,
                update_command=UpdateEstablishment(
                    is_active=is_active,
                    deleted_at=deleted_at,
                ),
            )
