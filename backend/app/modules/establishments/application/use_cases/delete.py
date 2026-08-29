import uuid
from datetime import UTC, datetime

from app.modules.establishments.application.ports.unit_of_work import (
    EstablishmentsUnitOfWorkProtocol,
)
from app.modules.establishments.domain.entities import UpdateEstablishment


class EstablishmentsDeleter:
    def __init__(self, uow: EstablishmentsUnitOfWorkProtocol) -> None:
        """
        Inicializa um removedor de estabelecimentos.

        Args:
            uow (EstablishmentsUnitOfWorkProtocol):
                Unit of work de estabelecimentos.
        """

        self._uow = uow

    async def delete(self, id_: uuid.UUID) -> None:
        """
        Remove (soft-delete) um estabelecimento, marcando `deleted_at`.

        Args:
            id_ (uuid.UUID):
                UUID do estabelecimento.
        """

        async with self._uow as uow:
            await uow.establishments.update(
                id_=id_,
                update_command=UpdateEstablishment(deleted_at=datetime.now(UTC)),
            )
