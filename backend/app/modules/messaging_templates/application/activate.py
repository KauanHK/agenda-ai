import uuid

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.application._authz import assert_can_write
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.domain.schemas import MessagingTemplateRead
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)


class MessagingTemplatesActivator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def activate(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateRead:
        return await self._set_active(
            template_id, is_active=True, actor=actor, establishment_id=establishment_id
        )

    async def deactivate(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateRead:
        return await self._set_active(
            template_id, is_active=False, actor=actor, establishment_id=establishment_id
        )

    async def _set_active(
        self,
        template_id: uuid.UUID,
        is_active: bool,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateRead:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)
            template = await repo.get_by_id(template_id)
            self._assert_scope(template, establishment_id)
            template.is_active = is_active
            updated = await repo.update(template)
            return MessagingTemplateRead.model_validate(updated)

    def _assert_scope(
        self, template: MessagingTemplate, establishment_id: uuid.UUID
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
