import uuid

from app.db.unit_of_work import UnitOfWork
from app.modules.establishments.domain.schemas import (
    EstablishmentRead,
    EstablishmentUpdate,
)
from app.modules.establishments.infra.repository import EstablishmentsRepository


class EstablishmentsUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        id: uuid.UUID,
        establishment_update: EstablishmentUpdate,
    ) -> EstablishmentRead:
        """
        Atualiza um estabelecimento existente.

        Args:
            id (uuid.UUID): O ID do estabelecimento a ser atualizado.
            establishment_update (EstablishmentUpdate): Os dados para atualização do estabelecimento.

        Returns:
             EstablishmentRead: O estabelecimento atualizado.
        """

        async with self._uow:
            repo = self._uow.repository(EstablishmentsRepository)
            establishment = await repo.get_by_id(id)

            for field, value in establishment_update.model_dump(
                exclude_unset=True
            ).items():
                setattr(establishment, field, value)

            updated = await repo.update(establishment)
            return EstablishmentRead.model_validate(updated)
