import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.application._authz import assert_can_access
from app.modules.messaging_templates.domain.filters import MessagingTemplateFilters
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.domain.schemas import (
    MessagingTemplateListItem,
    MessagingTemplateRead,
    ServiceRef,
)
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)
from app.modules.services.infra.repository import ServicesRepository


class MessagingTemplatesReader:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateRead:
        assert_can_access(actor, establishment_id)
        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)
            services_repo = self._uow.repository(ServicesRepository)
            template = await repo.get_by_id(template_id)
            self._assert_scope(template, establishment_id)
            links = await repo.list_services_for_template(template_id)
            service_refs: list[ServiceRef] = []
            for link in links:
                service = await services_repo.get_by_id(link.service_id)
                service_refs.append(ServiceRef(id=service.id, name=service.name))
            return MessagingTemplateRead.model_validate(template).model_copy(
                update={"services": service_refs}
            )

    async def paginate(
        self,
        pagination: PaginationParams,
        actor: UserActor,
        establishment_id: uuid.UUID,
        filters: MessagingTemplateFilters | None = None,
    ) -> PaginatedResponse[MessagingTemplateRead]:
        assert_can_access(actor, establishment_id)
        filters = filters or MessagingTemplateFilters()
        scoped = MessagingTemplateFilters(
            establishment_id=establishment_id,
            is_active=filters.is_active,
            service_id=filters.service_id,
            q=filters.q,
        )
        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)
            templates = await repo.list(pagination=pagination, filters=scoped)
            total = await repo.count(filters=scoped)
            return build_paginated_response(
                items=[MessagingTemplateListItem.model_validate(t) for t in templates],
                total=total,
                params=pagination,
            )

    def _assert_scope(
        self, template: MessagingTemplate, establishment_id: uuid.UUID
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
