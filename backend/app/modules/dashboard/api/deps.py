from typing import Annotated

from fastapi import Depends

from app.api.deps import UnitOfWorkDep
from app.modules.dashboard.application.dashboard import Dashboard
from app.modules.dashboard.domain.schemas import DashboardQueryParams


def get_dashboard_use_case(
    uow: UnitOfWorkDep,
) -> Dashboard:
    """Dependência do use case de dashboard."""

    return Dashboard(uow=uow)


def get_dashboard_query_params(
    query_params: Annotated[DashboardQueryParams, Depends()],
) -> DashboardQueryParams:
    """Dependência dos parâmetros de consulta do dashboard."""

    return query_params


DashboardDep = Annotated[
    Dashboard,
    Depends(get_dashboard_use_case),
]

DashboardQueryParamsDep = Annotated[
    DashboardQueryParams,
    Depends(get_dashboard_query_params),
]
