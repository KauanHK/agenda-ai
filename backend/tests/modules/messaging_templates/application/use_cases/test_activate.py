import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.messaging_templates.application.use_cases.activate import (
    MessagingTemplatesActivator,
)
from app.modules.messaging_templates.domain.entities import UpdateMessagingTemplate
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_template,
)


async def test_activate_sets_is_active_true(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.update.return_value = template

    result = await MessagingTemplatesActivator(uow).activate(
        template.id, admin_user, establishment_id
    )

    assert result == template
    sent: UpdateMessagingTemplate = templates_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.is_active is True


async def test_deactivate_sets_is_active_false(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.update.return_value = template

    await MessagingTemplatesActivator(uow).deactivate(
        template.id, admin_user, establishment_id
    )

    sent: UpdateMessagingTemplate = templates_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.is_active is False


async def test_activate_raises_not_found_for_other_tenant(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.get_by_id.return_value = make_template(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Template não encontrado"):
        await MessagingTemplatesActivator(uow).activate(
            uuid.uuid7(), admin_user, establishment_id
        )


async def test_activate_forbidden_for_member(
    uow, member_user, establishment_id, template
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await MessagingTemplatesActivator(uow).activate(
            template.id, member_user, establishment_id
        )
