import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.modules.messaging_templates.application.read import MessagingTemplatesReader
from app.modules.messaging_templates.domain.schemas import MessagingTemplateListItem, MessagingTemplateRead
from tests.modules.messaging_templates.application.conftest import make_link


@pytest.fixture
def reader(mock_uow) -> MessagingTemplatesReader:
    return MessagingTemplatesReader(uow=mock_uow)


@pytest.fixture
def pagination() -> PaginationParams:
    return PaginationParams(page=1, size=10)


async def test_get_by_id_returns_messaging_template_read(
    reader, admin_user, establishment_id, template_model
):
    result = await reader.get_by_id(template_model.id, admin_user, establishment_id)

    assert isinstance(result, MessagingTemplateRead)
    assert result.id == template_model.id


async def test_get_by_id_populates_services_from_junction_table(
    reader, mock_template_repo, mock_services_repo, admin_user, establishment_id, template_model, service_model
):
    link = make_link(template_model.id, service_model.id, template_model.type)
    mock_template_repo.list_services_for_template.return_value = [link]

    result = await reader.get_by_id(template_model.id, admin_user, establishment_id)

    assert len(result.services) == 1
    assert result.services[0].id == service_model.id
    assert result.services[0].name == service_model.name


async def test_get_by_id_raises_not_found_for_other_tenant(
    reader, admin_user, establishment_id, template_model
):
    template_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError):
        await reader.get_by_id(template_model.id, admin_user, establishment_id)


async def test_get_by_id_forbidden_for_global_admin(
    reader, global_admin_user, establishment_id, template_model
):
    with pytest.raises(ForbiddenError):
        await reader.get_by_id(template_model.id, global_admin_user, establishment_id)


async def test_get_by_id_allowed_for_member(reader, member_user, establishment_id, template_model):
    result = await reader.get_by_id(template_model.id, member_user, establishment_id)

    assert isinstance(result, MessagingTemplateRead)


async def test_paginate_returns_paginated_response(reader, pagination, admin_user, establishment_id):
    result = await reader.paginate(pagination, admin_user, establishment_id)

    assert isinstance(result, PaginatedResponse)
    assert len(result.data) == 1
    assert result.total == 1


async def test_paginate_returns_list_items_without_services(
    reader, pagination, admin_user, establishment_id
):
    result = await reader.paginate(pagination, admin_user, establishment_id)

    assert isinstance(result.data[0], MessagingTemplateListItem)
    assert "services" not in MessagingTemplateListItem.model_fields


async def test_paginate_scopes_to_establishment(
    reader, mock_template_repo, pagination, admin_user, establishment_id
):
    await reader.paginate(pagination, admin_user, establishment_id)

    filters = mock_template_repo.list.call_args[1]["filters"]
    assert filters.establishment_id == establishment_id


async def test_paginate_forbidden_for_global_admin(
    reader, pagination, global_admin_user, establishment_id
):
    with pytest.raises(ForbiddenError):
        await reader.paginate(pagination, global_admin_user, establishment_id)


async def test_paginate_returns_empty(reader, mock_template_repo, pagination, admin_user, establishment_id):
    mock_template_repo.list.return_value = []
    mock_template_repo.count.return_value = 0

    result = await reader.paginate(pagination, admin_user, establishment_id)

    assert result.data == []
    assert result.total == 0
