import uuid
from typing import Protocol

from app.modules.operating_hours.domain.entities import (
    NewOperatingHour,
    OperatingHour,
)


class OperatingHoursRepositoryProtocol(Protocol):
    async def list_by_establishment(
        self,
        establishment_id: uuid.UUID,
    ) -> list[OperatingHour]: ...

    async def replace_all(
        self,
        establishment_id: uuid.UUID,
        hours: list[NewOperatingHour],
    ) -> list[OperatingHour]: ...
