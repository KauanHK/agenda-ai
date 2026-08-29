import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.types import UNSET
from app.modules.messaging_templates.application.dtos.commands import (
    UpdateMessagingTemplateCommand,
)
from app.modules.messaging_templates.application.use_cases.update import (
    MessagingTemplatesUpdater,
)
from app.modules.messaging_templates.domain.entities import UpdateMessagingTemplate
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_template,
)


async def test_update_returns_entity(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.update.return_value = template

    result = await MessagingTemplatesUpdater(uow).update(
        template.id,
        UpdateMessagingTemplateCommand(name="Novo nome"),
        admin_user,
        establishment_id,
    )

    assert result == template


async def test_update_sends_only_defined_values(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.update.return_value = template

    await MessagingTemplatesUpdater(uow).update(
        template.id,
        UpdateMessagingTemplateCommand(name="Novo nome"),
        admin_user,
        establishment_id,
    )

    sent: UpdateMessagingTemplate = templates_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.name == "Novo nome"
    assert sent.content is UNSET
    assert sent.is_active is UNSET


async def test_update_can_change_is_active(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.update.return_value = template

    await MessagingTemplatesUpdater(uow).update(
        template.id,
        UpdateMessagingTemplateCommand(is_active=False),
        admin_user,
        establishment_id,
    )

    sent: UpdateMessagingTemplate = templates_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.is_active is False


async def test_update_raises_not_found_for_other_tenant(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.get_by_id.return_value = make_template(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Template não encontrado"):
        await MessagingTemplatesUpdater(uow).update(
            uuid.uuid7(),
            UpdateMessagingTemplateCommand(name="Novo nome"),
            admin_user,
            establishment_id,
        )


async def test_update_raises_conflict_on_integrity_error(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template
    templates_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Nome de template"):
        await MessagingTemplatesUpdater(uow).update(
            template.id,
            UpdateMessagingTemplateCommand(name="Duplicado"),
            admin_user,
            establishment_id,
        )


async def test_update_forbidden_for_member(
    uow, member_user, establishment_id, template
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await MessagingTemplatesUpdater(uow).update(
            template.id,
            UpdateMessagingTemplateCommand(name="Novo nome"),
            member_user,
            establishment_id,
        )


async def test_update_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, template
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await MessagingTemplatesUpdater(uow).update(
            template.id,
            UpdateMessagingTemplateCommand(name="Novo nome"),
            global_admin_user,
            establishment_id,
        )
