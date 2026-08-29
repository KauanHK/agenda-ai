import uuid

from sqlalchemy.exc import IntegrityError

from app.core.actors.user import UserActor
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.messaging_templates.application.authz import assert_can_write
from app.modules.messaging_templates.application.dtos.commands import (
    UpdateMessagingTemplateCommand,
)
from app.modules.messaging_templates.application.ports.unit_of_work import (
    MessagingTemplatesUnitOfWorkProtocol,
)
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    UpdateMessagingTemplate,
)


class MessagingTemplatesUpdater:
    def __init__(self, uow: MessagingTemplatesUnitOfWorkProtocol) -> None:
        """
        Inicializa um atualizador de templates de mensagem.

        Args:
            uow (MessagingTemplatesUnitOfWorkProtocol):
                Unit of work de templates de mensagem.
        """

        self._uow = uow

    async def update(
        self,
        template_id: uuid.UUID,
        data: UpdateMessagingTemplateCommand,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> MessagingTemplate:
        """
        Atualiza um template de mensagem.

        Args:
            template_id (uuid.UUID):
                Id do template a ser atualizado.
            data (UpdateMessagingTemplateCommand):
                Dados a serem atualizados no template.
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                Estabelecimento ao qual o template deve pertencer.

        Raises:
            NotFoundError:
                Se o template não existir ou pertencer a outro estabelecimento.
            ConflictError:
                Se o novo nome já estiver em uso no estabelecimento.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            template = await uow.messaging_templates.get_by_id(template_id)
            self._assert_scope(template, establishment_id)

            try:
                return await uow.messaging_templates.update(
                    id_=template_id,
                    update_command=UpdateMessagingTemplate(**data.defined_values()),
                )
            except IntegrityError as e:
                raise ConflictError(
                    "Nome de template já cadastrado neste estabelecimento."
                ) from e

    def _assert_scope(
        self,
        template: MessagingTemplate,
        establishment_id: uuid.UUID,
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
