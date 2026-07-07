from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DashboardFilters:
    start_date: datetime
    end_date: datetime
