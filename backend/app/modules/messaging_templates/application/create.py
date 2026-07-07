import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.db.unit_of_work import UnitOfWork
from app.modules.messaging_templates.application._authz import assert_can_write
from app.modules.messaging_templates.domain.model import MessagingTemplate
from app.modules.messaging_templates.domain.schemas import (
    MessagingTemplateCreate,
    MessagingTemplateRead,
)
from app.modules.messaging_templates.infra.repository import (
    MessagingTemplatesRepository,
)


class MessagingTemplatesCreator:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def create(
        self,
        data: MessagingTemplateCreate,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplateRead:
        assert_can_write(actor, establishment_id)

        async with self._uow:
            repo = self._uow.repository(MessagingTemplatesRepository)

            template = MessagingTemplate(
                establishment_id=establishment_id,
                name=data.name,
                content=data.content,
                type=data.type,
                minutes_before=data.minutes_before,
            )

            try:
                template = await repo.create(template)
            except IntegrityError as e:
                raise ConflictError(
                    "Nome de template já cadastrado neste estabelecimento."
                ) from e

            return MessagingTemplateRead.model_validate(template)
