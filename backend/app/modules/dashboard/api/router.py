import uuid

from fastapi import APIRouter

from app.modules.dashboard.api.deps import DashboardDep, DashboardQueryParamsDep
from app.modules.dashboard.domain.filters import DashboardFilters
from app.modules.dashboard.domain.schemas import DashboardSchema

router = APIRouter()


@router.get("")
async def get_dashboard(
    establishment_id: uuid.UUID,
    query_params: DashboardQueryParamsDep,
    dashboard: DashboardDep,
) -> DashboardSchema:
    """Retorna os dados do dashboard para um estabelecimento específico."""

    return await dashboard.get(
        establishment_id=establishment_id,
        filters=DashboardFilters(
            start_date=query_params.start_date,
            end_date=query_params.end_date,
        ),
    )
