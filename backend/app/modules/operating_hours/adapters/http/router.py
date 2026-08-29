import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.modules.operating_hours.adapters.http.dependencies import (
    OperatingHoursReaderDep,
    OperatingHoursUpdaterDep,
)
from app.modules.operating_hours.adapters.http.schemas import (
    OperatingHourRead,
    OperatingHoursUpdate,
)
from app.modules.operating_hours.application.dtos.commands import (
    OperatingHourItemCommand,
    ReplaceOperatingHoursCommand,
)

router = APIRouter()


@router.get("", response_model=list[OperatingHourRead])
async def get_operating_hours(
    establishment_id: uuid.UUID,
    reader: OperatingHoursReaderDep,
    actor: ActorDep,
) -> list[OperatingHourRead]:
    hours = await reader.list(actor, establishment_id)
    return [OperatingHourRead.model_validate(h.to_dict()) for h in hours]


@router.put("", response_model=list[OperatingHourRead])
async def update_operating_hours(
    establishment_id: uuid.UUID,
    data: OperatingHoursUpdate,
    updater: OperatingHoursUpdaterDep,
    actor: ActorDep,
) -> list[OperatingHourRead]:
    command = ReplaceOperatingHoursCommand(
        items=[
            OperatingHourItemCommand(
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
            )
            for item in data.items
        ]
    )
    hours = await updater.update(command, actor, establishment_id)
    return [OperatingHourRead.model_validate(h.to_dict()) for h in hours]
