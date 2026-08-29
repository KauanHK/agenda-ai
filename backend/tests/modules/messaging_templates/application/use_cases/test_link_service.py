import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.messaging_templates.application.use_cases.link_service import (
    MessagingTemplatesServiceLinker,
)
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_link,
    make_service,
    make_template,
)


async def test_link_creates_link(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    service = make_service(establishment_id)
    link = make_link(template.id, service.id)
    templates_repo.get_by_id.return_value = template
    services_query.get_by_id.return_value = service
    templates_repo.add_service_link.return_value = link

    result = await MessagingTemplatesServiceLinker(uow).link(
        template.id, service.id, admin_user, establishment_id
    )

    assert result == link
    templates_repo.add_service_link.assert_awaited_once_with(
        template.id, service.id, template.type
    )


async def test_link_same_type_raises_conflict(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    service = make_service(establishment_id)
    templates_repo.get_by_id.return_value = template
    services_query.get_by_id.return_value = service
    templates_repo.add_service_link.side_effect = IntegrityError(
        None, None, Exception()
    )

    with pytest.raises(ConflictError, match="já possui um template"):
        await MessagingTemplatesServiceLinker(uow).link(
            template.id, service.id, admin_user, establishment_id
        )


async def test_link_template_from_other_establishment_raises_not_found(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.get_by_id.return_value = make_template(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Template não encontrado"):
        await MessagingTemplatesServiceLinker(uow).link(
            uuid.uuid7(), uuid.uuid7(), admin_user, establishment_id
        )


async def test_link_service_from_other_establishment_raises_not_found(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    services_query.get_by_id.return_value = make_service(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Serviço não encontrado"):
        await MessagingTemplatesServiceLinker(uow).link(
            template.id, uuid.uuid7(), admin_user, establishment_id
        )


async def test_unlink_removes_link(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    service = make_service(establishment_id)
    templates_repo.get_by_id.return_value = template
    services_query.get_by_id.return_value = service
    templates_repo.get_link_or_none.return_value = make_link(template.id, service.id)

    await MessagingTemplatesServiceLinker(uow).unlink(
        template.id, service.id, admin_user, establishment_id
    )

    templates_repo.remove_service_link.assert_awaited_once_with(template.id, service.id)


async def test_unlink_raises_not_found_when_link_missing(
    uow, templates_repo, services_query, admin_user, establishment_id, template
):
    service = make_service(establishment_id)
    templates_repo.get_by_id.return_value = template
    services_query.get_by_id.return_value = service
    templates_repo.get_link_or_none.return_value = None

    with pytest.raises(NotFoundError, match="Vínculo não encontrado"):
        await MessagingTemplatesServiceLinker(uow).unlink(
            template.id, service.id, admin_user, establishment_id
        )


async def test_link_forbidden_for_member(uow, member_user, establishment_id, template):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await MessagingTemplatesServiceLinker(uow).link(
            template.id, uuid.uuid7(), member_user, establishment_id
        )


async def test_link_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, template
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await MessagingTemplatesServiceLinker(uow).link(
            template.id, uuid.uuid7(), global_admin_user, establishment_id
        )
