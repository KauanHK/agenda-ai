import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import UpdateUser


class UsersDeleter:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um removedor de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def delete(self, id: uuid.UUID, actor: UserActor) -> None:
        """Remove um usuário. Restrito a administradores globais."""

        if not actor.is_global_admin:
            raise ForbiddenError("Acesso negado.")

        async with self._uow as uow:
            await uow.users.update(id_=id, update_command=UpdateUser())
