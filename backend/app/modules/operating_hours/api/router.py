import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep
from app.modules.operating_hours.api.deps import (
    OperatingHoursReaderDep,
    OperatingHoursUpdaterDep,
)
from app.modules.operating_hours.domain.schemas import (
    OperatingHourRead,
    OperatingHoursUpdate,
)

router = APIRouter()


@router.get("", response_model=list[OperatingHourRead])
async def get_operating_hours(
    establishment_id: uuid.UUID,
    reader: OperatingHoursReaderDep,
    actor: ActorDep,
) -> list[OperatingHourRead]:
    return await reader.list(actor, establishment_id)


@router.put("", response_model=list[OperatingHourRead])
async def update_operating_hours(
    establishment_id: uuid.UUID,
    data: OperatingHoursUpdate,
    updater: OperatingHoursUpdaterDep,
    actor: ActorDep,
) -> list[OperatingHourRead]:
    return await updater.update(data, actor, establishment_id)
