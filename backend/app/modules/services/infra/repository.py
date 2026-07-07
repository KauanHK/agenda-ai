import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.services.domain.filters import ServiceFilters
from app.modules.services.domain.model import Service


class ServicesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(
        self,
        service_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Service | None:
        """Retorna o serviço com o id informado ou None caso não exista."""
        service = await self._session.get(Service, service_id)
        if service is None:
            return None
        if not include_deleted and service.deleted_at is not None:
            return None
        return service

    async def get_by_id(
        self,
        service_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Service:
        """Retorna o serviço com o id informado, levantando NotFoundError se ausente."""
        service = await self.get_by_id_or_none(service_id, include_deleted=include_deleted)
        if service is None:
            raise NotFoundError("Service not found.")
        return service

    async def create(self, service: Service) -> Service:
        """Persiste um novo serviço e o retorna já com os campos atualizados."""
        self._session.add(service)
        await self._session.flush()
        await self._session.refresh(service)
        return service

    async def update(self, service: Service) -> Service:
        """Atualiza um serviço existente e retorna a instância gerenciada."""
        merged = await self._session.merge(service)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def list(
        self,
        pagination: PaginationParams,
        filters: ServiceFilters | None = None,
        include_deleted: bool = False,
    ) -> list[Service]:
        """Lista serviços aplicando filtros e paginação."""
        query = self._construct_select_query(filters, include_deleted=include_deleted)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(
        self,
        filters: ServiceFilters | None = None,
        include_deleted: bool = False,
    ) -> int:
        """Retorna a quantidade total de serviços que satisfazem os filtros."""
        query = select(func.count()).select_from(  # pylint: disable=not-callable
            self._construct_select_query(filters, include_deleted=include_deleted).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    def _construct_select_query(
        self,
        filters: ServiceFilters | None = None,
        include_deleted: bool = False,
    ) -> Select[tuple[Service]]:
        query = select(Service)
        if not include_deleted:
            query = query.where(Service.deleted_at.is_(None))
        if filters is None:
            return query
        if filters.establishment_id is not None:
            query = query.where(Service.establishment_id == filters.establishment_id)
        if filters.is_active is not None:
            query = query.where(Service.is_active == filters.is_active)
        if filters.q is not None:
            like = f"%{filters.q}%"
            query = query.where(
                or_(
                    Service.name.ilike(like),
                    Service.description.ilike(like),
                )
            )
        return query
