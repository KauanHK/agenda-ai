import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import UpdateUser, User


class UsersActivator:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um ativador de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def activate(self, id: uuid.UUID, actor: UserActor) -> User:
        """Ativa um usuário."""

        return await self._set_active_status(id_=id, is_active=True, actor=actor)

    async def deactivate(self, id: uuid.UUID, actor: UserActor) -> User:
        """Inativa um usuário."""

        return await self._set_active_status(id_=id, is_active=False, actor=actor)

    async def _set_active_status(
        self,
        id_: uuid.UUID,
        is_active: bool,
        actor: UserActor,
    ) -> User:
        async with self._uow as uow:
            await uow.users.get_by_id(id_)

            if not actor.is_global_admin:
                raise ForbiddenError("Acesso negado.")

            return await uow.users.update(
                id_=id_,
                update_command=UpdateUser(is_active=is_active),
            )
