import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination.params import Page, PageParams
from app.modules.messaging_templates.application.dtos.filters import (
    MessagingTemplateFilters,
)
from app.modules.messaging_templates.application.use_cases.read import (
    MessagingTemplatesReader,
)
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_link,
    make_service,
    make_template,
)


async def test_get_by_id_returns_detail(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.list_services_for_template.return_value = []

    detail = await MessagingTemplatesReader(uow).get_by_id(
        template.id, admin_user, establishment_id
    )

    assert detail.template == template
    assert detail.services == ()


async def test_get_by_id_populates_linked_services(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    service = make_service(establishment_id)
    templates_repo.get_by_id.return_value = template
    templates_repo.list_services_for_template.return_value = [
        make_link(template.id, service.id)
    ]
    services_query.get_by_id.return_value = service

    detail = await MessagingTemplatesReader(uow).get_by_id(
        template.id, admin_user, establishment_id
    )

    assert len(detail.services) == 1
    assert detail.services[0].id == service.id
    assert detail.services[0].name == service.name


async def test_get_by_id_raises_not_found_for_other_tenant(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.get_by_id.return_value = make_template(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Template não encontrado"):
        await MessagingTemplatesReader(uow).get_by_id(
            uuid.uuid7(), admin_user, establishment_id
        )


async def test_get_by_id_allowed_for_member(
    uow, templates_repo, member_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.list_services_for_template.return_value = []

    detail = await MessagingTemplatesReader(uow).get_by_id(
        template.id, member_user, establishment_id
    )

    assert detail.template == template


async def test_get_by_id_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await MessagingTemplatesReader(uow).get_by_id(
            uuid.uuid7(), global_admin_user, establishment_id
        )


async def test_paginate_returns_page(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.paginate.return_value = Page(
        items=[template], total=1, page=1, page_size=10
    )

    page = await MessagingTemplatesReader(uow).paginate(
        PageParams(page=1, page_size=10), admin_user, establishment_id
    )

    assert page.total == 1
    assert page.items == [template]


async def test_paginate_scopes_filters_to_establishment(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.paginate.return_value = Page(items=[], total=0, page=1, page_size=10)
    service_id = uuid.uuid7()

    await MessagingTemplatesReader(uow).paginate(
        PageParams(page=1, page_size=10),
        admin_user,
        establishment_id,
        filters=MessagingTemplateFilters(
            establishment_id=uuid.uuid7(),  # deve ser sobrescrito
            is_active=True,
            service_id=service_id,
            q="lembrete",
        ),
    )

    sent: MessagingTemplateFilters = templates_repo.paginate.call_args.kwargs["filters"]
    assert sent.establishment_id == establishment_id
    assert sent.is_active is True
    assert sent.service_id == service_id
    assert sent.q == "lembrete"


async def test_paginate_returns_empty(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.paginate.return_value = Page(items=[], total=0, page=1, page_size=10)

    page = await MessagingTemplatesReader(uow).paginate(
        PageParams(page=1, page_size=10), admin_user, establishment_id
    )

    assert page.total == 0
    assert page.items == []


async def test_paginate_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await MessagingTemplatesReader(uow).paginate(
            PageParams(page=1, page_size=10), global_admin_user, establishment_id
        )
