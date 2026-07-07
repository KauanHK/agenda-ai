from datetime import datetime, time
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.modules.common.domain.schemas import BaseSchema
from app.modules.schedulings.domain.schemas import SchedulingRead


def _start_of_today() -> datetime:
    return datetime.combine(datetime.today(), time.min)


def _end_of_today() -> datetime:
    return datetime.combine(datetime.today(), time.max)


StartDate = Annotated[
    datetime,
    Field(default_factory=_start_of_today),
]

EndDate = Annotated[
    datetime,
    Field(default_factory=_end_of_today),
]


class DashboardSchema(BaseSchema):
    today_total: int
    today_confirmed: int
    pending_count: int
    expected_revenue: Decimal
    agenda: list[SchedulingRead]


class DashboardQueryParams(BaseSchema):
    start_date: StartDate
    end_date: EndDate
