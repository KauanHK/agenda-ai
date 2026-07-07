from typing import Annotated

from fastapi import Depends, Query

from app.core.pagination import PaginationParams


def get_pagination_params(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
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
