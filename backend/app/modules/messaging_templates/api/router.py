import uuid

from fastapi import APIRouter

from app.api.deps import ActorDep, PaginationParamsDep
from app.core.pagination import PaginatedResponse
from app.modules.messaging_templates.api.deps import (
    MessagingTemplatesActivatorDep,
    MessagingTemplatesCreatorDep,
    MessagingTemplatesDeleterDep,
    MessagingTemplatesLinkerDep,
    MessagingTemplatesReaderDep,
    MessagingTemplatesUpdaterDep,
)
from app.modules.messaging_templates.domain.filters import MessagingTemplateFilters
from app.modules.messaging_templates.domain.schemas import (
    MessagingTemplateCreate,
    MessagingTemplateListItem,
    MessagingTemplateRead,
    MessagingTemplateUpdate,
    ServiceMessagingTemplateRead,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[MessagingTemplateListItem],
)
async def list_messaging_templates(
    establishment_id: uuid.UUID,
    pagination: PaginationParamsDep,
    reader: MessagingTemplatesReaderDep,
    actor: ActorDep,
    is_active: bool | None = None,
    service_id: uuid.UUID | None = None,
    q: str | None = None,
) -> PaginatedResponse[MessagingTemplateRead]:
    return await reader.paginate(
        pagination=pagination,
        actor=actor,
        establishment_id=establishment_id,
        filters=MessagingTemplateFilters(
            is_active=is_active, service_id=service_id, q=q
        ),
    )


@router.get(
    "/{template_id}",
    response_model=MessagingTemplateRead,
)
async def get_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    reader: MessagingTemplatesReaderDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    return await reader.get_by_id(template_id, actor, establishment_id)


@router.post(
    "",
    response_model=MessagingTemplateRead,
    status_code=201,
)
async def create_messaging_template(
    establishment_id: uuid.UUID,
    data: MessagingTemplateCreate,
    creator: MessagingTemplatesCreatorDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    return await creator.create(data, actor, establishment_id)


@router.patch(
    "/{template_id}",
    response_model=MessagingTemplateRead,
)
async def update_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    data: MessagingTemplateUpdate,
    updater: MessagingTemplatesUpdaterDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    return await updater.update(template_id, data, actor, establishment_id)


@router.delete(
    "/{template_id}",
    status_code=204,
)
async def delete_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    deleter: MessagingTemplatesDeleterDep,
    actor: ActorDep,
) -> None:
    await deleter.delete(template_id, actor, establishment_id)


@router.post(
    "/{template_id}/services/{service_id}",
    response_model=ServiceMessagingTemplateRead,
    status_code=201,
)
async def link_service_to_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    service_id: uuid.UUID,
    linker: MessagingTemplatesLinkerDep,
    actor: ActorDep,
) -> ServiceMessagingTemplateRead:
    return await linker.link(template_id, service_id, actor, establishment_id)


@router.delete(
    "/{template_id}/services/{service_id}",
    status_code=204,
)
async def unlink_service_from_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    service_id: uuid.UUID,
    linker: MessagingTemplatesLinkerDep,
    actor: ActorDep,
) -> None:
    await linker.unlink(template_id, service_id, actor, establishment_id)


@router.post(
    "/{template_id}/activate",
    response_model=MessagingTemplateRead,
)
async def activate_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    activator: MessagingTemplatesActivatorDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    return await activator.activate(template_id, actor, establishment_id)


@router.post(
    "/{template_id}/deactivate",
    response_model=MessagingTemplateRead,
)
async def deactivate_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    activator: MessagingTemplatesActivatorDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    return await activator.deactivate(template_id, actor, establishment_id)
