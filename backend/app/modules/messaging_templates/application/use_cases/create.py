import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError
from app.modules.messaging_templates.application.authz import assert_can_write
from app.modules.messaging_templates.application.dtos.commands import (
    CreateMessagingTemplateCommand,
)
from app.modules.messaging_templates.application.ports.unit_of_work import (
    MessagingTemplatesUnitOfWorkProtocol,
)
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    NewMessagingTemplate,
)


class MessagingTemplatesCreator:
    def __init__(self, uow: MessagingTemplatesUnitOfWorkProtocol) -> None:
        """
        Inicializa um criador de templates de mensagem.

        Args:
            uow (MessagingTemplatesUnitOfWorkProtocol):
                Unit of work de templates de mensagem.
        """

        self._uow = uow

    async def create(
        self,
        data: CreateMessagingTemplateCommand,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplate:
        """
        Cria um template de mensagem para o estabelecimento.

        Args:
            data (CreateMessagingTemplateCommand):
                Dados do template a ser criado.
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                Estabelecimento ao qual o template pertence.

        Raises:
            ConflictError:
                Se já existir um template com o mesmo nome no estabelecimento.
        """

        assert_can_write(actor, establishment_id)

        new_template = NewMessagingTemplate(
            establishment_id=establishment_id,
            name=data.name,
            content=data.content,
            type=data.type,
            minutes_before=data.minutes_before,
        )

        async with self._uow as uow:
            try:
                return await uow.messaging_templates.create(new_template)
            except IntegrityError as e:
                raise ConflictError(
                    "Nome de template já cadastrado neste estabelecimento."
                ) from e
