import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.services.application._authz import assert_can_access
from app.modules.services.domain.filters import ServiceFilters
from app.modules.services.domain.model import Service
from app.modules.services.domain.schemas import ServiceRead
from app.modules.services.infra.repository import ServicesRepository


class ServicesReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        service_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> ServiceRead:
        """Retorna o serviço do estabelecimento especificado."""
        assert_can_access(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(ServicesRepository)
            service = await repo.get_by_id(service_id)
            self._assert_scope(service, establishment_id)
            return ServiceRead.model_validate(service)

    async def paginate(
        self,
        pagination: PaginationParams,
        filters: ServiceFilters,
    ) -> PaginatedResponse[ServiceRead]:
        """Retorna uma página de serviços conforme os filtros aplicados."""

        async with self._uow:
            repo = self._uow.repository(ServicesRepository)

            services = await repo.list(pagination=pagination, filters=filters)
            total = await repo.count(filters=filters)

            return build_paginated_response(
                items=[ServiceRead.model_validate(s) for s in services],
                total=total,
                params=pagination,
            )

    def _assert_scope(self, service: Service, establishment_id: uuid.UUID) -> None:
        if service.establishment_id != establishment_id:
            raise NotFoundError("Acesso negado.")
