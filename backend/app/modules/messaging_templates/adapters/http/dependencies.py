from typing import Annotated

from fastapi import Depends

from app.modules.messaging_templates.adapters.db.factories import make_unit_of_work
from app.modules.messaging_templates.adapters.db.unit_of_work import (
    MessagingTemplatesUnitOfWork,
)
from app.modules.messaging_templates.adapters.http.schemas import (
    MessagingTemplatesPaginationFilters,
)
from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)

MessagingTemplatesUnitOfWorkDep = Annotated[
    MessagingTemplatesUnitOfWork, Depends(make_unit_of_work)
]


def get_pagination_filters(
    query_params: Annotated[MessagingTemplatesPaginationFilters, Depends()],
) -> MessagingTemplateFilters:
    """Dependência para obter os filtros de paginação nos query params."""

    return MessagingTemplateFilters(
        is_active=query_params.is_active,
        service_id=query_params.service_id,
        q=query_params.q,
    )


PaginationFiltersDep = Annotated[
    MessagingTemplateFilters, Depends(get_pagination_filters)
]
