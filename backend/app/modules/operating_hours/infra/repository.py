import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.operating_hours.domain.model import OperatingHour


class OperatingHoursRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_establishment(
        self,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHour]:
        query = (
            select(OperatingHour)
            .where(OperatingHour.establishment_id == establishment_id)
            .order_by(OperatingHour.weekday)
        )
        result = await self._session.execute(query)
        return list(result.scalars())

    async def replace_all(
        self,
        establishment_id: uuid.UUID,
        hours: list[OperatingHour],
    ) -> list[OperatingHour]:
        await self._session.execute(
            delete(OperatingHour).where(
                OperatingHour.establishment_id == establishment_id
            )
        )
        for hour in hours:
            self._session.add(hour)
        await self._session.flush()
        for hour in hours:
            await self._session.refresh(hour)
        return hours
