from datetime import UTC, datetime

from app.core.pagination import PaginationParams
from app.db.unit_of_work import UnitOfWork
from app.modules.agent.actors import ClientAgentActor
from app.modules.schedulings.domain.enums import SchedulingStatus
from app.modules.schedulings.domain.filters import SchedulingFilters
from app.modules.schedulings.infra.repository import SchedulingsRepository


class AgentSchedulingsReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list(self, actor: ClientAgentActor) -> list[dict]:
        async with self._uow:
            repo = self._uow.repository(SchedulingsRepository)

            filters = SchedulingFilters(
                client_id=actor.client_id,
                establishment_id=actor.establishment_id,
                starts_at_from=datetime.now(UTC),
            )
            schedulings = await repo.list(
                pagination=PaginationParams(page=1, size=50),
                filters=filters,
            )

        return [
            {
                "scheduling_id": str(s.id),
                "starts_at": s.starts_at.isoformat(),
                "ends_at": s.ends_at.isoformat(),
                "status": s.status.value,
                "service_name": s.service.name,
            }
            for s in schedulings
            if s.status != SchedulingStatus.CANCELLED
        ]
