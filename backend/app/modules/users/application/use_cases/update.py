import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.users.application.dtos.commands import UpdateUserCommand
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import UpdateUser, User


class UsersUpdater:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um atualizador de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def update(
        self,
        id_: uuid.UUID,
        data: UpdateUserCommand,
        actor: UserActor,
    ) -> User:
        """Atualiza um usuário. Restrito a administradores globais."""

        update_command = UpdateUser(**data.defined_values())
        try:
            async with self._uow as uow:
                await uow.users.get_by_id(id_)

                if not actor.is_global_admin:
                    raise ForbiddenError("Acesso negado.")

                return await uow.users.update(
                    id_=id_,
                    update_command=update_command,
                )
        except IntegrityError as e:
            raise ConflictError("E-mail já está em uso.") from e

    async def update_me(
        self,
        data: UpdateUserCommand,
        actor: UserActor,
    ) -> User:
        """Atualiza os dados do próprio usuário autenticado."""

        update_command = UpdateUser(**data.defined_values())
        try:
            async with self._uow as uow:
                return await uow.users.update(
                    id_=actor.user_id,
                    update_command=update_command,
                )
        except IntegrityError as e:
            raise ConflictError("E-mail já está em uso.") from e
