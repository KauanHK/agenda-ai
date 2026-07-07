import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.messaging_templates.application.create import MessagingTemplatesCreator
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.domain.schemas import MessagingTemplateCreate, MessagingTemplateRead
from tests.modules.messaging_templates.application.conftest import make_actor


@pytest.fixture
def creator(mock_uow) -> MessagingTemplatesCreator:
    return MessagingTemplatesCreator(uow=mock_uow)


@pytest.fixture
def payload() -> MessagingTemplateCreate:
    return MessagingTemplateCreate(
        name="Template de Confirmação",
        content="Sua consulta foi confirmada!",
        type="confirmation",
    )


async def test_create_returns_messaging_template_read(creator, admin_user, establishment_id, payload):
    result = await creator.create(payload, admin_user, establishment_id)

    assert isinstance(result, MessagingTemplateRead)


async def test_create_calls_repo_scoped_to_establishment(
    creator, mock_template_repo, admin_user, establishment_id, payload
):
    await creator.create(payload, admin_user, establishment_id)

    mock_template_repo.create.assert_awaited_once()
    sent: MessagingTemplate = mock_template_repo.create.call_args[0][0]
    assert sent.establishment_id == establishment_id
    assert sent.name == payload.name
    assert sent.content == payload.content
    assert sent.type == payload.type


async def test_create_raises_conflict_on_integrity_error(
    creator, mock_template_repo, admin_user, establishment_id, payload
):
    mock_template_repo.create.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError):
        await creator.create(payload, admin_user, establishment_id)


async def test_create_forbidden_for_member(creator, member_user, establishment_id, payload):
    with pytest.raises(ForbiddenError):
        await creator.create(payload, member_user, establishment_id)


async def test_create_forbidden_for_global_admin(creator, global_admin_user, establishment_id, payload):
    with pytest.raises(ForbiddenError):
        await creator.create(payload, global_admin_user, establishment_id)


async def test_create_forbidden_when_not_member(creator, establishment_id, payload):
    actor = make_actor()

    with pytest.raises(ForbiddenError):
        await creator.create(payload, actor, establishment_id)
