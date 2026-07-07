from collections.abc import Sequence
from math import ceil

from pydantic import BaseModel, Field, computed_field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calcula o offset com base na página atual e no tamanho da página."""
        return (self.page - 1) * self.size


class PaginatedResponse[T](BaseModel):
    data: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)

    @computed_field
    def total_pages(self) -> int:
        """
        Calcula o número total de páginas com base
        no total de itens e no tamanho da página.
        """
        return ceil(self.total / self.size) if self.total > 0 else 0


def build_paginated_response[T](
    *,
    items: Sequence[T],
    total: int,
    params: PaginationParams,
) -> PaginatedResponse[T]:
    """
    Constrói uma resposta paginada com base nos itens fornecidos,
    total de itens e parâmetros de paginação.

    Args:
        items (Sequence[T]):
            A sequência de itens para a página atual.
        total (int):
            O número total de itens disponíveis.
        params (PaginationParams):
            Os parâmetros de paginação, incluindo página e tamanho.

    Returns:
        PaginatedResponse[T]:
            A resposta paginada contendo os itens, total, página e tamanho.
    """

    return PaginatedResponse[T](
        data=list(items),
        total=total,
        page=params.page,
        size=params.size,
    )
