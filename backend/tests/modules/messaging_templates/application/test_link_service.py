import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.messaging_templates.application.link_service import MessagingTemplatesServiceLinker
from app.modules.messaging_templates.domain.schemas import ServiceMessagingTemplateRead
from tests.modules.messaging_templates.application.conftest import make_actor


@pytest.fixture
def linker(mock_uow) -> MessagingTemplatesServiceLinker:
    return MessagingTemplatesServiceLinker(uow=mock_uow)


async def test_link_returns_service_messaging_template_read(
    linker, admin_user, establishment_id, template_model, service_model
):
    result = await linker.link(template_model.id, service_model.id, admin_user, establishment_id)

    assert isinstance(result, ServiceMessagingTemplateRead)


async def test_link_passes_template_type_to_repo(
    linker, mock_template_repo, admin_user, establishment_id, template_model, service_model
):
    await linker.link(template_model.id, service_model.id, admin_user, establishment_id)

    mock_template_repo.add_service_link.assert_awaited_once_with(
        template_model.id, service_model.id, template_model.type
    )


async def test_link_same_type_raises_conflict(
    linker, mock_template_repo, admin_user, establishment_id, template_model, service_model
):
    mock_template_repo.add_service_link.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError):
        await linker.link(template_model.id, service_model.id, admin_user, establishment_id)


async def test_link_template_from_other_establishment_raises_not_found(
    linker, admin_user, establishment_id, template_model, service_model
):
    template_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Template"):
        await linker.link(template_model.id, service_model.id, admin_user, establishment_id)


async def test_link_service_from_other_establishment_raises_not_found(
    linker, admin_user, establishment_id, template_model, service_model
):
    service_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError, match="Serviço"):
        await linker.link(template_model.id, service_model.id, admin_user, establishment_id)


async def test_unlink_removes_link(
    linker, mock_template_repo, admin_user, establishment_id, template_model, service_model
):
    await linker.unlink(template_model.id, service_model.id, admin_user, establishment_id)

    mock_template_repo.remove_service_link.assert_awaited_once_with(template_model.id, service_model.id)


async def test_unlink_raises_not_found_when_link_missing(
    linker, mock_template_repo, admin_user, establishment_id, template_model, service_model
):
    mock_template_repo.get_link_or_none.return_value = None

    with pytest.raises(NotFoundError, match="Vínculo"):
        await linker.unlink(template_model.id, service_model.id, admin_user, establishment_id)


async def test_link_forbidden_for_member(
    linker, member_user, establishment_id, template_model, service_model
):
    with pytest.raises(ForbiddenError):
        await linker.link(template_model.id, service_model.id, member_user, establishment_id)


async def test_link_forbidden_for_global_admin(
    linker, global_admin_user, establishment_id, template_model, service_model
):
    with pytest.raises(ForbiddenError):
        await linker.link(template_model.id, service_model.id, global_admin_user, establishment_id)
