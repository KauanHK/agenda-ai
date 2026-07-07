from datetime import time
from typing import Annotated

from pydantic import UUID7, Field, model_validator

from app.modules.common.domain.schemas import BaseSchema, EstablishmentScoped

Weekday = Annotated[int, Field(ge=0, le=6)]


class OperatingHourItem(BaseSchema):
    weekday: Weekday
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_times(self) -> OperatingHourItem:
        if self.start_time >= self.end_time:
            raise ValueError("start_time deve ser anterior a end_time")
        return self


class OperatingHourRead(OperatingHourItem, EstablishmentScoped):
    id: UUID7


class OperatingHoursUpdate(BaseSchema):
    items: list[OperatingHourItem]
