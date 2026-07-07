import uuid
from datetime import UTC, datetime

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.users.infra.repository import UsersRepository


class UsersDeleter:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def delete(self, id: uuid.UUID, actor: UserActor) -> None:
        if not actor.is_global_admin:
            raise ForbiddenError("Acesso negado.")

        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = await repo.get_by_id(id)
            user.deleted_at = datetime.now(UTC)
            await repo.update(user)
