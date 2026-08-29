import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.messaging_templates.application.dtos.commands import (
    CreateMessagingTemplateCommand,
)
from app.modules.messaging_templates.application.use_cases.create import (
    MessagingTemplatesCreator,
)
from app.modules.messaging_templates.domain.entities import NewMessagingTemplate
from app.modules.messaging_templates.domain.enums import TemplateType
from tests.modules.messaging_templates.application.use_cases.conftest import (
    make_actor,
    make_template,
)


@pytest.fixture
def payload() -> CreateMessagingTemplateCommand:
    return CreateMessagingTemplateCommand(
        name="Lembrete padrão",
        content="Olá {cliente}, seu horário é {data}.",
        type=TemplateType.REMINDER,
        minutes_before=60,
    )


async def test_create_returns_entity(
    uow, templates_repo, admin_user, establishment_id, payload
):
    templates_repo.create.return_value = make_template(establishment_id)

    result = await MessagingTemplatesCreator(uow).create(
        payload, admin_user, establishment_id
    )

    assert result.establishment_id == establishment_id


async def test_create_scopes_command_to_establishment(
    uow, templates_repo, admin_user, establishment_id, payload
):
    templates_repo.create.return_value = make_template(establishment_id)

    await MessagingTemplatesCreator(uow).create(payload, admin_user, establishment_id)

    templates_repo.create.assert_awaited_once()
    sent: NewMessagingTemplate = templates_repo.create.call_args[0][0]
    assert sent.establishment_id == establishment_id
    assert sent.name == payload.name
    assert sent.content == payload.content
    assert sent.type == payload.type
    assert sent.minutes_before == payload.minutes_before


async def test_create_raises_conflict_on_duplicate_name(
    uow, templates_repo, admin_user, establishment_id, payload
):
    templates_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError, match="Nome de template"):
        await MessagingTemplatesCreator(uow).create(
            payload, admin_user, establishment_id
        )


async def test_create_forbidden_for_member(uow, member_user, establishment_id, payload):
    with pytest.raises(ForbiddenError, match="establishment_admin"):
        await MessagingTemplatesCreator(uow).create(
            payload, member_user, establishment_id
        )


async def test_create_forbidden_for_global_admin(
    uow, global_admin_user, establishment_id, payload
):
    with pytest.raises(ForbiddenError, match="global_admin"):
        await MessagingTemplatesCreator(uow).create(
            payload, global_admin_user, establishment_id
        )


async def test_create_forbidden_when_not_member(uow, establishment_id, payload):
    actor = make_actor()

    with pytest.raises(ForbiddenError, match="Acesso negado"):
        await MessagingTemplatesCreator(uow).create(payload, actor, establishment_id)
