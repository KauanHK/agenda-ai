import uuid
from datetime import UTC, datetime

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.application._authz import assert_can_write
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)


class MessagingTemplatesDeleter:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def delete(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)
            template = await repo.get_by_id(template_id)
            self._assert_scope(template, establishment_id)
            template.deleted_at = datetime.now(UTC)
            await repo.update(template)

    def _assert_scope(
        self, template: MessagingTemplate, establishment_id: uuid.UUID
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
