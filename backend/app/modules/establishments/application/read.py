import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.establishments.domain.filters import EstablishmentFilters
from app.modules.establishments.domain.schemas import EstablishmentRead
from app.modules.establishments.infra.repository import EstablishmentsRepository
from app.modules.memberships.infra.repository import MembershipRepository


class EstablishmentsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        establishment_id: uuid.UUID,
        actor: UserActor,
    ) -> EstablishmentRead:
        async with self._uow:
            if not actor.is_member_of(establishment_id):
                memberships_repo = self._uow.repository(MembershipRepository)
                user_establishment = (
                    await memberships_repo.get_by_user_and_establishment_or_none(
                        user_id=actor.user_id,
                        establishment_id=establishment_id,
                    )
                )
                if user_establishment is None:
                    raise NotFoundError("Estabelecimento não encontrado.")

            repo = self._uow.repository(EstablishmentsRepository)
            establishment = await repo.get_by_id(establishment_id)

            return EstablishmentRead.model_validate(establishment)

    async def paginate(
        self,
        pagination: PaginationParams,
        name: str | None = None,
        cnpj: str | None = None,
        timezone: str | None = None,
    ) -> PaginatedResponse[EstablishmentRead]:
        async with self._uow:
            repo = self._uow.repository(EstablishmentsRepository)

            filters = EstablishmentFilters(
                name=name,
                document=cnpj,
                timezone=timezone,
            )

            establishments = await repo.list(
                pagination=pagination,
                filters=filters,
            )

            total = await repo.count(filters=filters)

            establishments_read = [
                EstablishmentRead.model_validate(est) for est in establishments
            ]

            return build_paginated_response(
                items=establishments_read,
                total=total,
                params=pagination,
            )
