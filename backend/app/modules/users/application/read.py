import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.users.domain.expanded import UserReadExpanded
from app.modules.users.domain.filters import UserFilters
from app.modules.users.domain.model import User
from app.modules.users.domain.schemas import UserRead
from app.modules.users.infra.repository import UsersRepository


class UsersReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        id: uuid.UUID,
        actor: UserActor,
    ) -> UserReadExpanded:

        async with self._uow:
            repo = self._uow.repository(UsersRepository)
            user = await repo.get_by_id_expanded(id)
            self._assert_scope(user, actor)
            return UserReadExpanded.model_validate(user)

    async def paginate(
        self,
        pagination: PaginationParams,
        actor: UserActor,
        filters: UserFilters | None = None,
    ) -> PaginatedResponse[UserRead]:

        if not actor.is_global_admin:
            raise ForbiddenError(
                "Apenas administradores globais podem listar "
                "usuários de todos os estabelecimentos."
            )

        async with self._uow:
            repo = self._uow.repository(UsersRepository)

            users, total = (
                await repo.list(pagination=pagination, filters=filters),
                await repo.count(filters=filters),
            )
            return build_paginated_response(
                items=[UserRead.model_validate(u) for u in users],
                total=total,
                params=pagination,
            )

    def _assert_scope(self, user: User, actor: UserActor) -> None:
        if actor.is_global_admin:
            return
