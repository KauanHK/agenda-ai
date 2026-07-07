import uuid
from datetime import UTC, datetime

from app.db.unit_of_work import UnitOfWork
from app.modules.establishments.infra.repository import EstablishmentsRepository


class EstablishmentsDeleter:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def delete(self, id: uuid.UUID) -> None:
        async with self._uow:
            repo = self._uow.repository(EstablishmentsRepository)
            establishment = await repo.get_by_id(id)
            establishment.deleted_at = datetime.now(UTC)
            await repo.update(establishment)
