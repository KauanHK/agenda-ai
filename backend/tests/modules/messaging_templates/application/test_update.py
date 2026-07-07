import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.messaging_templates.application.update import MessagingTemplatesUpdater
from app.modules.messaging_templates.domain.schemas import MessagingTemplateRead, MessagingTemplateUpdate
from tests.modules.messaging_templates.application.conftest import make_actor


@pytest.fixture
def updater(mock_uow) -> MessagingTemplatesUpdater:
    return MessagingTemplatesUpdater(uow=mock_uow)


async def test_update_returns_messaging_template_read(
    updater, admin_user, establishment_id, template_model
):
    result = await updater.update(
        template_model.id, MessagingTemplateUpdate(name="Novo Nome"), admin_user, establishment_id
    )

    assert isinstance(result, MessagingTemplateRead)


async def test_update_only_updates_sent_fields(updater, admin_user, establishment_id, template_model):
    original_content = template_model.content
    original_type = template_model.type

    await updater.update(
        template_model.id, MessagingTemplateUpdate(name="Apenas Nome"), admin_user, establishment_id
    )

    assert template_model.name == "Apenas Nome"
    assert template_model.content == original_content
    assert template_model.type == original_type


async def test_update_raises_not_found_for_other_tenant(
    updater, admin_user, establishment_id, template_model
):
    template_model.establishment_id = uuid.uuid7()

    with pytest.raises(NotFoundError):
        await updater.update(
            template_model.id, MessagingTemplateUpdate(name="X"), admin_user, establishment_id
        )


async def test_update_raises_conflict_on_integrity_error(
    updater, mock_template_repo, admin_user, establishment_id, template_model
):
    mock_template_repo.update.side_effect = IntegrityError(None, None, Exception())

    with pytest.raises(ConflictError):
        await updater.update(
            template_model.id, MessagingTemplateUpdate(name="Existente"), admin_user, establishment_id
        )


async def test_update_forbidden_for_member(updater, member_user, establishment_id, template_model):
    with pytest.raises(ForbiddenError):
        await updater.update(
            template_model.id, MessagingTemplateUpdate(name="X"), member_user, establishment_id
        )


async def test_update_forbidden_for_global_admin(
    updater, global_admin_user, establishment_id, template_model
):
    with pytest.raises(ForbiddenError):
        await updater.update(
            template_model.id, MessagingTemplateUpdate(name="X"), global_admin_user, establishment_id
        )


async def test_update_can_change_is_active(updater, admin_user, establishment_id, template_model):
    template_model.is_active = True

    await updater.update(
        template_model.id, MessagingTemplateUpdate(is_active=False), admin_user, establishment_id
    )

    assert template_model.is_active is False
