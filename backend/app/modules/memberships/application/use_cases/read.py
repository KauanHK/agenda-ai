import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.core.pagination.params import Page, PageParams
from app.modules.memberships.application.ports.unit_of_work import (
    MembershipsUnitOfWorkProtocol,
)
from app.modules.memberships.domain.entities import (
    MembershipExpanded,
    MembershipWithUser,
)


class MembershipsReader:
    def __init__(self, uow: MembershipsUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de memberships.

        Args:
            uow (MembershipsUnitOfWorkProtocol):
                Unit of work de memberships.
        """

        self._uow = uow

    async def get_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> MembershipExpanded:
        """Obtém uma membership expandida (usuário e estabelecimento completos)."""

        async with self._uow as uow:
            if not actor.is_global_admin:
                caller = await uow.memberships.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
                if caller is None:
                    raise ForbiddenError("Acesso negado ao estabelecimento.")

            return await uow.memberships.get_by_user_and_establishment_expanded(
                user_id=user_id,
                establishment_id=establishment_id,
            )

    async def paginate(
        self,
        establishment_id: uuid.UUID,
        actor: UserActor,
        page_params: PageParams,
    ) -> Page[MembershipWithUser]:
        """Pagina os membros de um estabelecimento."""

        async with self._uow as uow:
            if not actor.is_global_admin:
                caller = await uow.memberships.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
                if caller is None:
                    raise ForbiddenError("Acesso negado ao estabelecimento.")

            items = await uow.memberships.list_by_establishment(
                establishment_id, page_params
            )
            total = await uow.memberships.count_by_establishment(establishment_id)

            return Page(
                items=items,
                total=total,
                page=page_params.page,
                page_size=page_params.page_size,
            )

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        actor: UserActor,
    ) -> list[MembershipWithUser]:
        """Lista as memberships de um usuário."""

        if not actor.is_global_admin and actor.user_id != user_id:
            raise ForbiddenError("Acesso negado.")

        async with self._uow as uow:
            return await uow.memberships.list_by_user(user_id)
