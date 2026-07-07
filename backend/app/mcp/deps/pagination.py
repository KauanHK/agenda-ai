from typing import Annotated

from fastmcp.dependencies import Depends

from app.core.pagination import PaginationParams


def get_pagination_params(
    page: int,
    size: int,
) -> PaginationParams:
    """
    Dependência para obter os parâmetros de paginação
    a partir dos parâmetros de consulta.
    """

    return PaginationParams(
        page=page,
        size=size,
    )


PaginationParamsDep = Annotated[PaginationParams, Depends(get_pagination_params)]
