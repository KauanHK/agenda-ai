from typing import Any

from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from app.core.actors.customer import CustomerActor
from app.db.deps import get_unit_of_work
from app.mcp.deps.auth import get_current_client_actor
from app.mcp.deps.pagination import PaginationParamsDep
from app.modules.services.application.read import ServicesReader
from app.modules.services.domain.filters import ServiceFilters


def register_tools(mcp: FastMCP) -> None:

    @mcp.tool
    async def get_services(
        pagination: PaginationParamsDep,
        actor: CustomerActor = Depends(get_current_client_actor),
    ) -> dict[str, Any]:
        """
        Lista os serviços disponíveis no estabelecimento.
        Use para apresentar ao cliente as opções de serviço antes de agendar.
        """

        # Por algum motivo o FastMCP não está injetando a dependência do UnitOfWorkDep
        uow = get_unit_of_work()

        reader = ServicesReader(uow=uow)
        try:
            services = await reader.paginate(
                pagination=pagination,
                filters=ServiceFilters(establishment_id=actor.establishment_id),
            )

            return {
                "success": True,
                "data": [
                    {
                        "service_id": str(s.id),
                        "name": s.name,
                        "description": s.description,
                        "duration_minutes": s.duration_minutes,
                        "price": str(s.price),
                    }
                    for s in services.data
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "error_code": "API_ERROR",
                "message": str(e),
            }
