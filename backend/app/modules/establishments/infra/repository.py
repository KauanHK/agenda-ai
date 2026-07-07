import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.establishments.domain.filters import EstablishmentFilters
from app.modules.establishments.domain.model import Establishment


class EstablishmentsRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, establishment: Establishment) -> Establishment:
        self._session.add(establishment)
        await self._session.flush()
        await self._session.refresh(establishment)
        return establishment

    async def get_by_id_or_none(
        self,
        id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Establishment | None:
        query = select(Establishment).where(Establishment.id == id)
        if not include_deleted:
            query = query.where(Establishment.deleted_at.is_(None))
        result = await self._session.execute(query)
        return result.scalars().one_or_none()

    async def get_by_id(
        self,
        establishment_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Establishment:
        establishment = await self.get_by_id_or_none(establishment_id, include_deleted=include_deleted)
        if establishment is None:
            raise NotFoundError("Establishment not found")
        return establishment

    async def get_by_cnpj_or_none(self, cnpj: str) -> Establishment | None:
        result = await self._session.execute(
            select(Establishment).where(
                Establishment.document == cnpj,
                Establishment.deleted_at.is_(None),
            )
        )
        return result.scalars().one_or_none()

    async def get_by_cnpj(self, cnpj: str) -> Establishment:
        establishment = await self.get_by_cnpj_or_none(cnpj)
        if establishment is None:
            raise NotFoundError("Establishment not found")
        return establishment

    async def list(
        self,
        pagination: PaginationParams,
        filters: EstablishmentFilters | None = None,
        include_deleted: bool = False,
    ) -> list[Establishment]:
        query = self._construct_select_query(filters, include_deleted=include_deleted)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(
        self,
        filters: EstablishmentFilters | None = None,
        include_deleted: bool = False,
    ) -> int:
        query = select(func.count()).select_from(
            self._construct_select_query(filters, include_deleted=include_deleted).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def update(self, establishment: Establishment) -> Establishment:
        establishment = await self._session.merge(establishment)
        await self._session.refresh(establishment)
        return establishment

    def _construct_select_query(
        self,
        filters: EstablishmentFilters | None = None,
        include_deleted: bool = False,
    ) -> Select[tuple[Establishment]]:
        query = select(Establishment)
        if not include_deleted:
            query = query.where(Establishment.deleted_at.is_(None))
        if filters is not None:
            if filters.name is not None:
                query = query.where(Establishment.name.ilike(f"%{filters.name}%"))
            if filters.document is not None:
                query = query.where(Establishment.document == filters.document)
            if filters.timezone is not None:
                query = query.where(Establishment.timezone == filters.timezone)
        return query
