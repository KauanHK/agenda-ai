"""
Pacote de paginação.

Re-exporta os nomes públicos para manter compatibilidade com os imports antigos
(`from app.core.pagination import PaginationParams, ...`). A dependência FastAPI
`PageParamsDep` deve ser importada de `app.core.pagination.dependencies`, para não
exigir FastAPI em contextos que não são HTTP (ex.: worker).
"""

from app.core.pagination.params import Page, PageParams
from app.core.pagination.schemas import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    build_paginated_response_from_page,
)

__all__ = [
    "Page",
    "PageParams",
    "PaginatedResponse",
    "PaginationParams",
    "build_paginated_response",
    "build_paginated_response_from_page",
]
