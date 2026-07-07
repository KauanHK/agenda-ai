import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import PaginationParams
from app.modules.unavailabilities.domain.filters import UnavailabilityFilters
from app.modules.unavailabilities.domain.model import Unavailability


class UnavailabilitiesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id_or_none(self, unavailability_id: uuid.UUID) -> Unavailability | None:
        return await self._session.get(Unavailability, unavailability_id)

    async def get_by_id(self, unavailability_id: uuid.UUID) -> Unavailability:
        unavailability = await self.get_by_id_or_none(unavailability_id)
        if unavailability is None:
            raise NotFoundError("Unavailability not found.")
        return unavailability

    async def create(self, unavailability: Unavailability) -> Unavailability:
        self._session.add(unavailability)
        await self._session.flush()
        await self._session.refresh(unavailability)
        return unavailability

    async def update(self, unavailability: Unavailability) -> Unavailability:
        merged = await self._session.merge(unavailability)
        await self._session.flush()
        await self._session.refresh(merged)
        return merged

    async def delete(self, unavailability: Unavailability) -> None:
        await self._session.delete(unavailability)
        await self._session.flush()

    async def list(
        self,
        pagination: PaginationParams,
        filters: UnavailabilityFilters | None = None,
    ) -> list[Unavailability]:
        query = self._construct_select_query(filters)
        query = query.limit(pagination.size).offset(pagination.offset)
        result = await self._session.execute(query)
        return list(result.scalars())

    async def count(self, filters: UnavailabilityFilters | None = None) -> int:
        query = select(func.count()).select_from(  # pylint: disable=not-callable
            self._construct_select_query(filters).subquery()
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    def _construct_select_query(
        self,
        filters: UnavailabilityFilters | None = None,
    ) -> Select[tuple[Unavailability]]:
        query = select(Unavailability)
        if filters is None:
            return query
        if filters.establishment_id is not None:
            query = query.where(Unavailability.establishment_id == filters.establishment_id)
        if filters.starts_at_from is not None:
            query = query.where(Unavailability.starts_at >= filters.starts_at_from)
        if filters.starts_at_to is not None:
            query = query.where(Unavailability.starts_at <= filters.starts_at_to)
        return query
