from app.core.pagination.params import Page, PageParams
from app.modules.establishments.application.dtos.filters import EstablishmentFilters
from app.modules.establishments.application.ports.unit_of_work import (
    EstablishmentsUnitOfWorkProtocol,
)
from app.modules.establishments.domain.entities import Establishment


class EstablishmentsPaginator:
    def __init__(self, uow: EstablishmentsUnitOfWorkProtocol) -> None:
        """
        Inicializa um paginador de estabelecimentos.

        Args:
            uow (EstablishmentsUnitOfWorkProtocol):
                Unit of work de estabelecimentos.
        """

        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        filters: EstablishmentFilters | None = None,
    ) -> Page[Establishment]:
        """
        Pagina estabelecimentos com filtros opcionais.

        Args:
            page_params (PageParams):
                Parâmetros de paginação.
            filters (EstablishmentFilters):
                Filtros a serem aplicados.
        """

        async with self._uow as uow:
            return await uow.establishments.paginate(
                page_params=page_params,
                filters=filters,
            )
