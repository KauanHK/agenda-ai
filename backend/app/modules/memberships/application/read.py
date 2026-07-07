import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import ForbiddenError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.memberships.domain.expanded import MembershipReadExpanded
from app.modules.memberships.domain.schemas import MembershipRead
from app.modules.memberships.infra.repository import MembershipRepository


class MembershipsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_user_and_establishment(
        self,
        user_id: uuid.UUID,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> MembershipReadExpanded:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            if not actor.is_global_admin:
                caller = await repo.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
                if caller is None:
                    raise ForbiddenError("Acesso negado ao estabelecimento.")

            membership = await repo.get_by_user_and_establishment_expanded(
                user_id=user_id,
                establishment_id=establishment_id,
            )
            return MembershipReadExpanded.model_validate(membership)

    async def paginate(
        self,
        establishment_id: uuid.UUID,
        actor: UserActor,
        pagination: PaginationParams,
    ) -> PaginatedResponse[MembershipRead]:
        async with self._uow:
            repo = self._uow.repository(MembershipRepository)

            if not actor.is_global_admin:
                caller = await repo.get_by_user_and_establishment_or_none(
                    actor.user_id, establishment_id
                )
                if caller is None:
                    raise ForbiddenError("Acesso negado ao estabelecimento.")

            items = await repo.list_by_establishment(establishment_id, pagination)
            total = await repo.count_by_establishment(establishment_id)

            return build_paginated_response(
                items=[MembershipRead.model_validate(m) for m in items],
                total=total,
                params=pagination,
            )

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        actor: UserActor,
    ) -> list[MembershipRead]:
        if not actor.is_global_admin and actor.user_id != user_id:
            raise ForbiddenError("Acesso negado.")

        async with self._uow:
            repo = self._uow.repository(MembershipRepository)
            memberships = await repo.list_by_user(user_id)
            return [MembershipRead.model_validate(m) for m in memberships]
