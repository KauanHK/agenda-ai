from collections.abc import Sequence
from math import ceil

from pydantic import BaseModel, Field, computed_field

from app.core.pagination.params import Page


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


def build_paginated_response_from_page[T](page: Page[T]) -> PaginatedResponse[T]:
    """
    Constrói uma resposta paginada a partir de uma `Page` da camada de aplicação.

    Args:
        page (Page[T]):
            A página de resultados retornada por um repositório/use case.

    Returns:
        PaginatedResponse[T]:
            A resposta paginada correspondente, mantendo o contrato JSON atual
            (`data`, `total`, `page`, `size`, `total_pages`).
    """

    return PaginatedResponse[T](
        data=list(page.items),
        total=page.total,
        page=page.page,
        size=page.page_size,
    )
