import uuid

from app.modules.establishments.application.dtos.commands import (
    UpdateEstablishmentCommand,
)
from app.modules.establishments.application.ports.unit_of_work import (
    EstablishmentsUnitOfWorkProtocol,
)
from app.modules.establishments.domain.entities import (
    Establishment,
    UpdateEstablishment,
)


class EstablishmentsUpdater:
    def __init__(self, uow: EstablishmentsUnitOfWorkProtocol) -> None:
        """
        Inicializa um atualizador de estabelecimentos.

        Args:
            uow (EstablishmentsUnitOfWorkProtocol):
                Unit of work de estabelecimentos.
        """

        self._uow = uow

    async def update(
        self,
        id_: uuid.UUID,
        data: UpdateEstablishmentCommand,
    ) -> Establishment:
        """
        Atualiza um estabelecimento.

        Args:
            id_ (uuid.UUID):
                UUID do estabelecimento.
            data (UpdateEstablishmentCommand):
                Dados a serem atualizados no estabelecimento.
        """

        update_command = UpdateEstablishment(**data.defined_values())
        async with self._uow as uow:
            return await uow.establishments.update(
                id_=id_,
                update_command=update_command,
            )
