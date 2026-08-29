from dataclasses import dataclass
from datetime import time

from app.core.types import BaseCreateCommand


@dataclass(frozen=True, slots=True)
class OperatingHourItemCommand(BaseCreateCommand):
    weekday: int
    start_time: time
    end_time: time


@dataclass(frozen=True, slots=True)
class ReplaceOperatingHoursCommand(BaseCreateCommand):
    items: list[OperatingHourItemCommand]
