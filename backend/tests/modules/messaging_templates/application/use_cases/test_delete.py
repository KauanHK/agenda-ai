import uuid

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.types import UNSET
from app.modules.messaging_templates.application.use_cases.delete import (
    MessagingTemplatesDeleter,
)
from app.modules.messaging_templates.domain.entities import UpdateMessagingTemplate
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_template,
)


async def test_delete_marks_deleted_at(
    uow, templates_repo, admin_user, establishment_id, template
):
    templates_repo.get_by_id.return_value = template

    await MessagingTemplatesDeleter(uow).delete(
        template.id, admin_user, establishment_id
    )

    templates_repo.update.assert_awaited_once()
    sent: UpdateMessagingTemplate = templates_repo.update.call_args.kwargs[
        "update_command"
    ]
    assert sent.deleted_at is not UNSET
    assert sent.deleted_at is not None


async def test_delete_raises_not_found_for_other_tenant(
    uow, templates_repo, admin_user, establishment_id
):
    templates_repo.get_by_id.return_value = make_template(uuid.uuid7())

    with pytest.raises(NotFoundError, match="Template não encontrado"):
        await MessagingTemplatesDeleter(uow).delete(
            uuid.uuid7(), admin_user, establishment_id
        )


async def test_delete_forbidden_for_member(
    uow, member_user, establishment_id, template
):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await MessagingTemplatesDeleter(uow).delete(
            template.id, member_user, establishment_id
        )
