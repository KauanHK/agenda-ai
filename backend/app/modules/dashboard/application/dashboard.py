import uuid

from app.db.unit_of_work import UnitOfWork
from app.modules.dashboard.domain.filters import DashboardFilters
from app.modules.dashboard.domain.schemas import DashboardSchema
from app.modules.schedulings.domain.schemas import SchedulingRead
from app.modules.schedulings.infra.repository import SchedulingsRepository


class Dashboard:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get(
        self,
        establishment_id: uuid.UUID,
        filters: DashboardFilters,
    ) -> DashboardSchema:

        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)
            data = await repo.get_dashboard_by_establishment(
                establishment_id=establishment_id,
                filters=filters,
            )

        return DashboardSchema(
            today_total=data.total,
            today_confirmed=data.confirmed,
            pending_count=data.pending,
            expected_revenue=data.expected_revenue,
            agenda=[SchedulingRead.model_validate(s) for s in data.schedulings],
        )
