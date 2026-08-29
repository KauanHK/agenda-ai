import uuid

from fastapi import APIRouter

from app.api.deps.auth import ActorDep
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.params import Page
from app.core.pagination.schemas import (
    PaginatedResponse,
    build_paginated_response_from_page,
)
from app.modules.messaging_templates.adapters.http.dependencies import (
    MessagingTemplatesUnitOfWorkDep,
    PaginationFiltersDep,
)
from app.modules.messaging_templates.adapters.http.schemas import (
    MessagingTemplateCreate,
    MessagingTemplateListItem,
    MessagingTemplateRead,
    MessagingTemplateUpdate,
    ServiceMessagingTemplateRead,
)
from app.modules.messaging_templates.application.dtos.commands import (
    CreateMessagingTemplateCommand,
    UpdateMessagingTemplateCommand,
)
from app.modules.messaging_templates.application.use_cases.activate import (
    MessagingTemplatesActivator,
)
from app.modules.messaging_templates.application.use_cases.create import (
    MessagingTemplatesCreator,
)
from app.modules.messaging_templates.application.use_cases.delete import (
    MessagingTemplatesDeleter,
)
from app.modules.messaging_templates.application.use_cases.link_service import (
    MessagingTemplatesServiceLinker,
)
from app.modules.messaging_templates.application.use_cases.read import (
    MessagingTemplatesReader,
)
from app.modules.messaging_templates.application.use_cases.update import (
    MessagingTemplatesUpdater,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[MessagingTemplateListItem],
)
async def list_messaging_templates(
    establishment_id: uuid.UUID,
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> PaginatedResponse[MessagingTemplateListItem]:
    page = await MessagingTemplatesReader(uow=uow).paginate(
        page_params=page_params,
        actor=actor,
        establishment_id=establishment_id,
        filters=filters,
    )
    return build_paginated_response_from_page(
        Page(
            items=[
                MessagingTemplateListItem.model_validate(t.to_dict())
                for t in page.items
            ],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )
    )


@router.get(
    "/{template_id}",
    response_model=MessagingTemplateRead,
)
async def get_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    detail = await MessagingTemplatesReader(uow=uow).get_by_id(
        template_id, actor, establishment_id
    )
    return MessagingTemplateRead.model_validate(detail.to_dict())


@router.post(
    "",
    response_model=MessagingTemplateRead,
    status_code=201,
)
async def create_messaging_template(
    establishment_id: uuid.UUID,
    data: MessagingTemplateCreate,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    template = await MessagingTemplatesCreator(uow=uow).create(
        CreateMessagingTemplateCommand(**data.model_dump(exclude_unset=True)),
        actor,
        establishment_id,
    )
    return MessagingTemplateRead.model_validate(template.to_dict())


@router.patch(
    "/{template_id}",
    response_model=MessagingTemplateRead,
)
async def update_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    data: MessagingTemplateUpdate,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    template = await MessagingTemplatesUpdater(uow=uow).update(
        template_id,
        UpdateMessagingTemplateCommand(**data.model_dump(exclude_unset=True)),
        actor,
        establishment_id,
    )
    return MessagingTemplateRead.model_validate(template.to_dict())


@router.delete(
    "/{template_id}",
    status_code=204,
)
async def delete_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> None:
    await MessagingTemplatesDeleter(uow=uow).delete(template_id, actor, establishment_id)


@router.post(
    "/{template_id}/services/{service_id}",
    response_model=ServiceMessagingTemplateRead,
    status_code=201,
)
async def link_service_to_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    service_id: uuid.UUID,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> ServiceMessagingTemplateRead:
    link = await MessagingTemplatesServiceLinker(uow=uow).link(
        template_id, service_id, actor, establishment_id
    )
    return ServiceMessagingTemplateRead.model_validate(link.to_dict())


@router.delete(
    "/{template_id}/services/{service_id}",
    status_code=204,
)
async def unlink_service_from_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    service_id: uuid.UUID,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> None:
    await MessagingTemplatesServiceLinker(uow=uow).unlink(
        template_id, service_id, actor, establishment_id
    )


@router.post(
    "/{template_id}/activate",
    response_model=MessagingTemplateRead,
)
async def activate_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    template = await MessagingTemplatesActivator(uow=uow).activate(
        template_id, actor, establishment_id
    )
    return MessagingTemplateRead.model_validate(template.to_dict())


@router.post(
    "/{template_id}/deactivate",
    response_model=MessagingTemplateRead,
)
async def deactivate_messaging_template(
    establishment_id: uuid.UUID,
    template_id: uuid.UUID,
    uow: MessagingTemplatesUnitOfWorkDep,
    actor: ActorDep,
) -> MessagingTemplateRead:
    template = await MessagingTemplatesActivator(uow=uow).deactivate(
        template_id, actor, establishment_id
    )
    return MessagingTemplateRead.model_validate(template.to_dict())
