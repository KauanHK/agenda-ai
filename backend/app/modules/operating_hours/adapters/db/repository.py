import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.operating_hours.adapters.db.models import (
    OperatingHour as OperatingHourModel,
)
from app.modules.operating_hours.domain.entities import (
    NewOperatingHour,
    OperatingHour,
)


class OperatingHoursRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_establishment(
        self,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHour]:
        query = (
            select(OperatingHourModel)
            .where(OperatingHourModel.establishment_id == establishment_id)
            .order_by(OperatingHourModel.weekday)
        )
        result = await self._session.execute(query)
        return [self._to_entity(row) for row in result.scalars()]

    async def replace_all(
        self,
        establishment_id: uuid.UUID,
        hours: list[NewOperatingHour],
    ) -> list[OperatingHour]:
        await self._session.execute(
            delete(OperatingHourModel).where(
                OperatingHourModel.establishment_id == establishment_id
            )
        )
        rows = [OperatingHourModel(**hour.to_dict()) for hour in hours]
        for row in rows:
            self._session.add(row)
        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return [self._to_entity(row) for row in rows]

    def _to_entity(self, row: OperatingHourModel) -> OperatingHour:
        return OperatingHour(
            id=row.id,
            establishment_id=row.establishment_id,
            weekday=row.weekday,
            start_time=row.start_time,
            end_time=row.end_time,
        )
