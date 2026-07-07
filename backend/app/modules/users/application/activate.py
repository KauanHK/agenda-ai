import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.db.unit_of_work import UnitOfWork
from app.modules.users.domain.schemas import UserRead
from app.modules.users.infra.repository import UsersRepository


class UsersActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(self, id: uuid.UUID, actor: UserActor) -> UserRead:
        """Ativa um usuário."""
        return await self._set_active_status(id=id, is_active=True, actor=actor)

    async def deactivate(self, id: uuid.UUID, actor: UserActor) -> UserRead:
        """Inativa um usuário."""
        return await self._set_active_status(id=id, is_active=False, actor=actor)

    async def _set_active_status(
        self,
        id: uuid.UUID,
        is_active: bool,
        actor: UserActor,
    ) -> UserRead:
        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = await repo.get_by_id(id)

            if not actor.is_global_admin:
                raise ForbiddenError("Acesso negado.")

            user.is_active = is_active
            updated = await repo.update(user)
            return UserRead.model_validate(updated)
