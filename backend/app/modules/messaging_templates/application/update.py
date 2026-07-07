import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.application._authz import assert_can_write
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.domain.schemas import (
    MessagingTemplateRead,
    MessagingTemplateUpdate,
)
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)


class MessagingTemplatesUpdater:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def update(
        self,
        template_id: uuid.UUID,
        data: MessagingTemplateUpdate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateRead:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)

            template = await repo.get_by_id(template_id)
            self._assert_scope(template, establishment_id)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(template, field, value)

            try:
                template = await repo.update(template)
            except IntegrityError as e:
                raise ConflictError(
                    "Nome de template já cadastrado neste estabelecimento."
                ) from e

            return MessagingTemplateRead.model_validate(template)

    def _assert_scope(
        self, template: MessagingTemplate, establishment_id: uuid.UUID
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
