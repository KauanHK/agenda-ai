import uuid
from datetime import UTC, datetime

from app.core.actors.user import UserActor
from app.core.exceptions import NotFoundError
from app.modules.messaging_templates.application.authz import assert_can_write
from app.modules.messaging_templates.application.ports.unit_of_work import (
    MessagingTemplatesUnitOfWorkProtocol,
)
from app.modules.messaging_templates.domain.entities import (
    MessagingTemplate,
    UpdateMessagingTemplate,
)


class MessagingTemplatesDeleter:
    def __init__(self, uow: MessagingTemplatesUnitOfWorkProtocol) -> None:
        """
        Inicializa um removedor de templates de mensagem.

        Args:
            uow (MessagingTemplatesUnitOfWorkProtocol):
                Unit of work de templates de mensagem.
        """

        self._uow = uow

    async def delete(
        self,
        template_id: uuid.UUID,
        actor: UserActor,
        establishment_id: uuid.UUID,
    ) -> None:
        """
        Remove (logicamente) um template de mensagem.

        Args:
            template_id (uuid.UUID):
                Id do template a ser removido.
            actor (UserActor):
                Usuário que está executando a ação.
            establishment_id (uuid.UUID):
                Estabelecimento ao qual o template deve pertencer.

        Raises:
            NotFoundError:
                Se o template não existir ou pertencer a outro estabelecimento.
        """

        assert_can_write(actor, establishment_id)

        async with self._uow as uow:
            template = await uow.messaging_templates.get_by_id(template_id)
            self._assert_scope(template, establishment_id)
            await uow.messaging_templates.update(
                id_=template_id,
                update_command=UpdateMessagingTemplate(deleted_at=datetime.now(UTC)),
            )

    def _assert_scope(
        self,
        template: MessagingTemplate,
        establishment_id: uuid.UUID,
    ) -> None:
        if template.establishment_id != establishment_id:
            raise NotFoundError("Template não encontrado.")
