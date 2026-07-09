from typing import Annotated

from fastapi import Depends

from app.core.pagination.params import PageParams
from app.core.pagination.schemas import PaginationParams


def get_pagination_params(
    query_params: Annotated[PaginationParams, Depends()],
) -> PageParams:
    """
    Dependência para obter os parâmetros de paginação
    a partir dos parâmetros de consulta.
    """

    return PageParams(
        page=query_params.page,
        page_size=query_params.size,
    )


PageParamsDep = Annotated[
    PageParams,
    Depends(get_pagination_params),
]
