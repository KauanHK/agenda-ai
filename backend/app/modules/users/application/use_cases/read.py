import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.core.pagination.params import Page, PageParams
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import User, UserExpanded


class UsersReader:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def get_by_id(
        self,
        id: uuid.UUID,
        actor: UserActor,
    ) -> UserExpanded:
        """Obtém um usuário pelo seu id, com memberships aninhadas."""

        async with self._uow as uow:
            user = await uow.users.get_by_id_expanded(id)
            self._assert_scope(user, actor)
            return user

    async def paginate(
        self,
        page_params: PageParams,
        actor: UserActor,
        filters: UserFilters | None = None,
    ) -> Page[User]:
        """Pagina usuários. Restrito a administradores globais."""

        if not actor.is_global_admin:
            raise ForbiddenError(
                "Apenas administradores globais podem listar "
                "usuários de todos os estabelecimentos."
            )

        async with self._uow as uow:
            return await uow.users.paginate(page_params=page_params, filters=filters)

    def _assert_scope(self, user: UserExpanded, actor: UserActor) -> None:
        if actor.is_global_admin:
            return
